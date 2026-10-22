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
    assert tools == {"score_lead", "score_leads", "check_api_health"}


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
