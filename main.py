from fastapi import FastAPI
from pydantic import BaseModel

from service.osm_service import analizar_ubicacion

app = FastAPI()


class LocationRequest(BaseModel):
    lat: float
    lon: float
    tipo_negocio: str


@app.post("/analizar")
def analizar(req: LocationRequest):
    resultado = analizar_ubicacion(
        req.lat,
        req.lon,
        req.tipo_negocio
    )
    return resultado