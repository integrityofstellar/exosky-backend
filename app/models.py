from typing import List
from pydantic import BaseModel

class Coordinates(BaseModel):
    ra: float
    dec: float

