from __future__ import annotations

import json

import httpx
import pytest
from mcp.server.fastmcp.exceptions import ToolError

import server

LEAD = {
    "id": 660737,
    "origen": "API",
    "fuente": "Chat",
    "ult_actividad": "Page Visited on Website",
    "ocupacion": "Unemployed",
}


def _use_api(monkeypatch, handler):
    monkeypatch.setattr(server, "_transport", httpx.MockTransport(handler))


def _text(result) -> str:
    content = result[0] if isinstance(result, tuple) else result
    return content[0].text


async def test_expone_las_tres_herramientas():
    tools = {t.name for t in await server.mcp.list_tools()}
    assert tools == {"score_lead", "score_leads", "check_api_health", "explain_score"}


async def test_score_lead_envia_un_registro_y_devuelve_score_y_umbral(monkeypatch):
    recibido = {}

    def handler(request: httpx.Request) -> httpx.Response:
        recibido["path"] = request.url.path
        recibido["body"] = json.loads(request.content)
        return httpx.Response(200, json=[{"id": 660737, "score": 0.81, "prediccion": 1}])

    _use_api(monkeypatch, handler)
    result = await server.mcp.call_tool("score_lead", LEAD)

    assert recibido["path"] == "/predict"
    assert recibido["body"] == [LEAD]
    salida = json.loads(_text(result))
    assert salida == {"id": 660737, "score": 0.81, "prediccion": 1, "umbral": 0.5}


async def test_score_lead_sin_id_usa_cero(monkeypatch):
    recibido = {}

    def handler(request: httpx.Request) -> httpx.Response:
        recibido["body"] = json.loads(request.content)
        return httpx.Response(200, json=[{"id": 0, "score": 0.1, "prediccion": 0}])

    _use_api(monkeypatch, handler)
    await server.mcp.call_tool("score_lead", {"fuente": "Chat"})

    assert recibido["body"] == [{"id": 0, "fuente": "Chat"}]


async def test_score_leads_procesa_un_lote(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        ids = [r["id"] for r in json.loads(request.content)]
        return httpx.Response(
            200, json=[{"id": i, "score": 0.2, "prediccion": 0} for i in ids]
        )

    _use_api(monkeypatch, handler)
    result = await server.mcp.call_tool(
        "score_leads", {"leads": [{"id": 1}, {"id": 2}]}
    )

    salida = json.loads(_text(result))
    assert [r["id"] for r in salida["resultados"]] == [1, 2]
    assert salida["umbral"] == 0.5


async def test_error_de_validacion_de_la_api_se_explica_en_castellano(monkeypatch):
    detalle = [
        {"loc": ["body", 0, "visitas_total"], "msg": "Input should be less than or equal to 30"}
    ]
    _use_api(monkeypatch, lambda r: httpx.Response(422, json={"detail": detalle}))

    with pytest.raises(ToolError) as exc:
        await server.mcp.call_tool("score_lead", {"visitas_total": 99})

    assert "visitas_total" in str(exc.value)
    assert "rechaz" in str(exc.value).lower()


async def test_api_caida_devuelve_mensaje_claro(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    _use_api(monkeypatch, handler)
    with pytest.raises(ToolError) as exc:
        await server.mcp.call_tool("score_lead", LEAD)

    assert "no está disponible" in str(exc.value)


async def test_check_api_health(monkeypatch):
    _use_api(monkeypatch, lambda r: httpx.Response(200, json={"status": "ok"}))
    result = await server.mcp.call_tool("check_api_health", {})
    assert json.loads(_text(result))["status"] == "ok"


async def test_recurso_de_variables_documenta_limites_y_leakage():
    contenido = await server.mcp.read_resource("leadscoring://variables")
    texto = contenido[0].content
    for campo in ("visitas_total", "paginas_vistas_visita", "ult_actividad", "ocupacion"):
        assert campo in texto
    assert "30" in texto and "20" in texto


def _factor(variable, valor, contribucion, efecto):
    import math

    return {
        "variable": variable,
        "valor": valor,
        "contribucion_logit": contribucion,
        "efecto": efecto,
        "multiplicador_odds": math.exp(contribucion),
    }


EXPLICACION_API = {
    "id": 660737,
    "score": 0.153,
    "prediccion": 0,
    "logit": -1.71,
    "logit_referencia": -0.82,
    "score_referencia": 0.305,
    "factores": [
        _factor("tiempo_en_site_total", 0.0, -2.21, "baja"),
        _factor("fuente", "Chat", 1.35, "sube"),
        _factor("ocupacion", "Unemployed", 0.13, "sube"),
        _factor("ambito", "Select", -0.36, "baja"),
        _factor("score_actividad", 15.0, 0.47, "sube"),
        _factor("origen", "API", 0.0, "neutro"),
    ],
    "banderas": {
        "datos_faltantes": [],
        "variables_sensibles_leakage": ["ult_actividad", "ocupacion"],
    },
}


async def test_explain_score_llama_a_explain_y_devuelve_los_factores_principales(monkeypatch):
    recibido = {}

    def handler(request: httpx.Request) -> httpx.Response:
        recibido["path"] = request.url.path
        recibido["body"] = json.loads(request.content)
        return httpx.Response(200, json=[EXPLICACION_API])

    _use_api(monkeypatch, handler)
    result = await server.mcp.call_tool("explain_score", {**LEAD, "top": 3})

    assert recibido["path"] == "/explain"
    assert recibido["body"] == [LEAD]
    salida = json.loads(_text(result))
    assert salida["score"] == 0.153 and salida["umbral"] == 0.5
    assert [f["variable"] for f in salida["factores_principales"]] == [
        "tiempo_en_site_total", "fuente", "ocupacion",
    ]
    assert salida["factores_principales"][0]["efecto"] == "baja"
    assert salida["variables_no_mostradas"] == 3


async def test_explain_score_incluye_resumen_y_como_leerlo(monkeypatch):
    _use_api(monkeypatch, lambda r: httpx.Response(200, json=[EXPLICACION_API]))
    salida = json.loads(_text(await server.mcp.call_tool("explain_score", LEAD)))

    assert "15,3%" in salida["resumen"]
    assert "30,5%" in salida["resumen"]  # the average lead, the baseline of every factor
    assert "tiempo_en_site_total" in salida["resumen"]
    assert salida["score_referencia"] == 0.305
    assert "lead promedio" in salida["como_leerlo"]
    assert "chances" in salida["como_leerlo"]
    assert len(salida["factores_principales"]) == 5  # default top


async def test_explain_score_avisa_de_datos_faltantes_y_leakage(monkeypatch):
    explicacion = {
        **EXPLICACION_API,
        "banderas": {
            "datos_faltantes": ["score_actividad", "score_perfil"],
            "variables_sensibles_leakage": ["ocupacion"],
        },
    }
    _use_api(monkeypatch, lambda r: httpx.Response(200, json=[explicacion]))
    salida = json.loads(_text(await server.mcp.call_tool("explain_score", LEAD)))

    avisos = " ".join(salida["avisos"])
    assert "score_actividad" in avisos and "score_perfil" in avisos
    assert "ocupacion" in avisos and "DEC-014" in avisos


async def test_explain_score_sin_avisos_cuando_no_aplican(monkeypatch):
    explicacion = {
        **EXPLICACION_API,
        "banderas": {"datos_faltantes": [], "variables_sensibles_leakage": []},
    }
    _use_api(monkeypatch, lambda r: httpx.Response(200, json=[explicacion]))
    salida = json.loads(_text(await server.mcp.call_tool("explain_score", LEAD)))

    assert salida["avisos"] == []


async def test_explain_score_traduce_errores_de_la_api(monkeypatch):
    detalle = [{"loc": ["body", 0, "visitas_total"], "msg": "Input should be less than or equal to 30"}]
    _use_api(monkeypatch, lambda r: httpx.Response(422, json={"detail": detalle}))

    with pytest.raises(ToolError) as exc:
        await server.mcp.call_tool("explain_score", {"visitas_total": 99})

    assert "visitas_total" in str(exc.value)
