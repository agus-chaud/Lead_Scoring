"""MCP server that exposes the Lead Scoring API to MCP clients (e.g. Claude).

The server holds no model logic: every score comes from the FastAPI service
(`07_despliegue/api`), configured through SCORING_API_URL.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

API_URL = os.getenv("SCORING_API_URL", "http://127.0.0.1:8000")
TIMEOUT_SECONDS = 15.0
# Mirrors UMBRAL in api/scoring.py: the API only returns the 0/1 prediction.
UMBRAL = 0.5

# Overridden in tests to avoid real network calls.
_transport: httpx.AsyncBaseTransport | None = None

mcp = FastMCP("lead-scoring")

VARIABLES_DOC = """\
# Variables de entrada del scoring de leads

Todas son opcionales salvo `id` (si no se informa, se usa 0). Un campo ausente
se trata como dato faltante y el pipeline lo imputa.

| Campo | Tipo | Notas |
|---|---|---|
| id | entero | Identificador del lead; solo para trazabilidad, no predice. |
| origen | texto | Canal de origen del lead (p. ej. "API", "Lead Add Form"). |
| fuente | texto | Fuente de tráfico (p. ej. "Google", "Direct Traffic", "Chat", "Organic Search"). |
| no_enviar_email | texto | "Yes" / "No". |
| visitas_total | número | Máximo 30. Valores mayores son rechazados por la API. |
| tiempo_en_site_total | número | Tiempo total en el sitio, en segundos. |
| paginas_vistas_visita | número | Máximo 20. Valores mayores son rechazados por la API. |
| ult_actividad | texto | Última actividad registrada del lead. |
| ambito | texto | Ámbito del lead. |
| ocupacion | texto | Ocupación declarada. |
| score_actividad | número | Score de marketing automation; faltante en leads nuevos. |
| score_perfil | número | Score de marketing automation; faltante en leads nuevos. |
| descarga_lm | texto | "Yes" / "No". |

## Cómo leer el resultado

- `score`: probabilidad estimada de compra (0 a 1).
- `prediccion`: 1 si `score` >= 0,5, si no 0.
- `umbral`: el corte usado (0,5).

## Advertencia sobre `ult_actividad` y `ocupacion`

El rendimiento del modelo depende bastante de ambas y no se descarta que reflejen información
posterior al contacto comercial (posible leakage, ver DEC-014). La auditoría
estimó un ROC AUC de 0,8947 con ambas y de 0,8376 sin ellas. Si el lead se
puntúa antes de que esas variables existan, el score real será menos preciso.
"""


def _explain_validation_error(detail: Any) -> str:
    if not isinstance(detail, list):
        return str(detail)
    partes = []
    for error in detail:
        campo = ".".join(str(p) for p in error.get("loc", []) if p not in ("body", 0))
        partes.append(f"{campo or 'registro'}: {error.get('msg', 'valor inválido')}")
    return "; ".join(partes)


async def _request(method: str, path: str, **kwargs: Any) -> Any:
    try:
        async with httpx.AsyncClient(
            base_url=API_URL, timeout=TIMEOUT_SECONDS, transport=_transport
        ) as client:
            response = await client.request(method, path, **kwargs)
    except httpx.TransportError as exc:
        raise ToolError(
            f"La API de scoring no está disponible en {API_URL} ({type(exc).__name__}). "
            "Verificá que el servicio esté levantado."
        ) from exc

    if response.status_code == 422:
        motivo = _explain_validation_error(response.json().get("detail"))
        raise ToolError(f"La API rechazó los datos del lead: {motivo}")
    if response.is_error:
        raise ToolError(f"La API respondió con error {response.status_code}.")
    return response.json()


def _build_record(**campos: Any) -> dict[str, Any]:
    """Keep only the fields the caller informed; missing ones stay missing for the API."""
    return {k: v for k, v in campos.items() if v is not None}


@mcp.tool()
async def score_lead(
    id: int = 0,
    origen: str | None = None,
    fuente: str | None = None,
    no_enviar_email: str | None = None,
    visitas_total: float | None = None,
    tiempo_en_site_total: float | None = None,
    paginas_vistas_visita: float | None = None,
    ult_actividad: str | None = None,
    ambito: str | None = None,
    ocupacion: str | None = None,
    score_actividad: float | None = None,
    score_perfil: float | None = None,
    descarga_lm: str | None = None,
) -> dict[str, Any]:
    """Calcula la probabilidad de compra de UN lead con el modelo de scoring.

    Informá los datos que tengas; los que falten se tratan como faltantes.
    Devuelve `score` (probabilidad 0-1), `prediccion` (1 si score >= umbral) y `umbral`.
    Consultá el recurso leadscoring://variables para el significado de cada campo.
    """
    registro = _build_record(
        id=id, origen=origen, fuente=fuente, no_enviar_email=no_enviar_email,
        visitas_total=visitas_total, tiempo_en_site_total=tiempo_en_site_total,
        paginas_vistas_visita=paginas_vistas_visita, ult_actividad=ult_actividad,
        ambito=ambito, ocupacion=ocupacion, score_actividad=score_actividad,
        score_perfil=score_perfil, descarga_lm=descarga_lm,
    )
    resultados = await _request("POST", "/predict", json=[registro])
    return {**resultados[0], "umbral": UMBRAL}


COMO_LEERLO = (
    "Cada factor compara al lead con un lead promedio (el de `score_referencia`): sube o baja "
    "sus chances (odds) de compra respecto de uno típico. x2 las duplica y x0,5 las reduce a la "
    "mitad. El score final sale de combinar todos los factores multiplicándolos, no de sumar "
    "puntos porcentuales. En los datos numéricos (tiempo en el sitio, páginas por visita y los "
    "scores) el efecto sigue una curva (splines): el mismo aumento puede pesar mucho en valores "
    "bajos y casi nada en valores altos."
)


def _numero(valor: float, decimales: int = 1) -> str:
    return f"{valor:.{decimales}f}".replace(".", ",")


def _frase_factor(factor: dict[str, Any]) -> str:
    multiplicador = _numero(factor["multiplicador_odds"], 2)
    verbo = {"sube": "aumenta las chances", "baja": "reduce las chances"}.get(
        factor["efecto"], "no cambia las chances"
    )  # always relative to the average lead
    valor = "sin dato" if factor["valor"] is None else factor["valor"]
    return f"{factor['variable']} = {valor} {verbo} (x{multiplicador})"


def _avisos(banderas: dict[str, list[str]]) -> list[str]:
    avisos = []
    if banderas["datos_faltantes"]:
        avisos.append(
            f"Faltan datos de: {', '.join(banderas['datos_faltantes'])}. "
            "El modelo los trata como valores desconocidos, así que el resultado es menos confiable."
        )
    if banderas["variables_sensibles_leakage"]:
        avisos.append(
            f"{', '.join(banderas['variables_sensibles_leakage'])}: el rendimiento del modelo depende "
            "bastante de esta variable y no se descarta que refleje información posterior al contacto comercial "
            "(posible leakage, DEC-014)."
        )
    return avisos


@mcp.tool()
async def explain_score(
    id: int = 0,
    origen: str | None = None,
    fuente: str | None = None,
    no_enviar_email: str | None = None,
    visitas_total: float | None = None,
    tiempo_en_site_total: float | None = None,
    paginas_vistas_visita: float | None = None,
    ult_actividad: str | None = None,
    ambito: str | None = None,
    ocupacion: str | None = None,
    score_actividad: float | None = None,
    score_perfil: float | None = None,
    descarga_lm: str | None = None,
    top: int = 5,
) -> dict[str, Any]:
    """Explica CÓMO se llega al score de UN lead: qué variables lo suben o lo bajan y cuánto.

    Usa los mismos campos que `score_lead` más `top` (cuántos factores mostrar, por defecto 5).
    El modelo es una regresión logística con splines: en los datos numéricos continuos (tiempo
    en el sitio, páginas por visita y los dos scores) el efecto sigue una curva en vez de una
    recta, así que el mismo cambio no pesa igual en todos los rangos. Como el modelo suma el
    aporte de cada dato por separado, la explicación es exacta, no una aproximación.
    Si el usuario pregunta qué son los splines, por qué superan a la regresión logística
    tradicional o cómo se comprobó (validación cruzada y validation.pkl), usá el recurso
    `leadscoring://ficha-modelo`.
    Devuelve el `resumen` en lenguaje natural, los `factores_principales` ordenados por impacto,
    `avisos` (datos faltantes, posible leakage) y `como_leerlo` para interpretar los multiplicadores.
    """
    registro = _build_record(
        id=id, origen=origen, fuente=fuente, no_enviar_email=no_enviar_email,
        visitas_total=visitas_total, tiempo_en_site_total=tiempo_en_site_total,
        paginas_vistas_visita=paginas_vistas_visita, ult_actividad=ult_actividad,
        ambito=ambito, ocupacion=ocupacion, score_actividad=score_actividad,
        score_perfil=score_perfil, descarga_lm=descarga_lm,
    )
    explicacion = (await _request("POST", "/explain", json=[registro]))[0]
    principales = explicacion["factores"][: max(1, top)]

    conclusion = "se predice compra" if explicacion["prediccion"] else "no se predice compra"
    resumen = (
        f"Probabilidad de compra estimada: {_numero(explicacion['score'] * 100)}% "
        f"(umbral {_numero(UMBRAL * 100, 0)}%: {conclusion}). Un lead promedio tiene "
        f"{_numero(explicacion['score_referencia'] * 100)}%. Frente a ese lead promedio, lo que más pesa: "
        + "; ".join(_frase_factor(f) for f in principales[:3])
        + "."
    )
    return {
        "id": explicacion["id"],
        "score": explicacion["score"],
        "prediccion": explicacion["prediccion"],
        "umbral": UMBRAL,
        "score_referencia": explicacion["score_referencia"],
        "resumen": resumen,
        "factores_principales": principales,
        "variables_no_mostradas": len(explicacion["factores"]) - len(principales),
        "avisos": _avisos(explicacion["banderas"]),
        "como_leerlo": COMO_LEERLO,
    }


@mcp.tool()
async def score_leads(leads: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcula la probabilidad de compra de VARIOS leads en una sola llamada.

    Cada elemento de `leads` usa los mismos campos que `score_lead` y debe llevar un `id`
    único para poder relacionar cada resultado. Si un lead es inválido la API rechaza
    todo el lote y el error indica el campo.
    """
    resultados = await _request("POST", "/predict", json=leads)
    return {"resultados": resultados, "umbral": UMBRAL}


@mcp.tool()
async def check_api_health() -> dict[str, Any]:
    """Verifica que la API de scoring esté levantada y respondiendo."""
    return await _request("GET", "/health")


FICHA_PATH = Path(__file__).resolve().parent / "ficha_modelo.md"


@mcp.resource("leadscoring://ficha-modelo", mime_type="text/markdown")
def ficha_modelo() -> str:
    """Ficha del modelo en lenguaje simple: qué hace, qué tan bien funciona y sus límites."""
    return FICHA_PATH.read_text(encoding="utf-8")


@mcp.resource("leadscoring://variables", mime_type="text/markdown")
def variables() -> str:
    """Diccionario de variables de entrada, límites y cómo interpretar el resultado."""
    return VARIABLES_DOC


if __name__ == "__main__":
    mcp.run()
