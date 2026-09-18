from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class RegistroEntrada(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Annotated[int, Field(..., alias="id")]
    origen: Annotated[str | None, Field(default=None, alias="origen")]
    fuente: Annotated[str | None, Field(default=None, alias="fuente")]
    no_enviar_email: Annotated[str | None, Field(default=None, alias="no_enviar_email")]
    visitas_total: Annotated[float | None, Field(default=None, alias="visitas_total", le=30)]
    tiempo_en_site_total: Annotated[float | None, Field(default=None, alias="tiempo_en_site_total")]
    paginas_vistas_visita: Annotated[float | None, Field(default=None, alias="paginas_vistas_visita", le=20)]
    ult_actividad: Annotated[str | None, Field(default=None, alias="ult_actividad")]
    ambito: Annotated[str | None, Field(default=None, alias="ambito")]
    ocupacion: Annotated[str | None, Field(default=None, alias="ocupacion")]
    score_actividad: Annotated[float | None, Field(default=None, alias="score_actividad")]
    score_perfil: Annotated[float | None, Field(default=None, alias="score_perfil")]
    descarga_lm: Annotated[str | None, Field(default=None, alias="descarga_lm")]


class ScoringSalida(BaseModel):
    id: int
    score: float
    prediccion: int
