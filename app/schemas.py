from pydantic import BaseModel
from typing import List, Optional


class Exoplanet(BaseModel):
    pl_name: str
    ra: float
    dec: float
    sy_dist: Optional[float]
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

class ExoplanetsResponse(BaseModel):
    data: List[Exoplanet]
    metadata: dict

class Star(BaseModel):
    SOURCE_ID: int
    ra: float
    dec: float
    phot_g_mean_mag: float
    parallax: float
    x: float
    y: float
    z: float
    intensity: float

class StarsResponse(BaseModel):
    data: List[Star]
    metadata: dict

class SaveConstellationRequest(BaseModel):
    author: str
    name: str
    stars: List[str]

class ConstellationSchema(BaseModel):
    name: str
    author: str
    stars: List[str]