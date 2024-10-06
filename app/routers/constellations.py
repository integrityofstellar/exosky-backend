import os
from typing import List
import requests
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import Constellation, ConstellationCreate, SessionLocal, create_constellation
from app.schemas import ConstellationSchema, ExoplanetsResponse, SaveConstellationRequest, Star
from ..services import fetch_exoplanets_data, celestial_to_xyz
import json

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/constellations/")
def save_constellations(constellation: ConstellationCreate, db: Session = Depends(get_db)):
    return create_constellation(db, constellation)


@router.get("/constellations/")
def get_constellations(planet: str, db: Session = Depends(get_db)):
    constellations = db.query(Constellation).filter(Constellation.planet == planet).all()
    if not constellations:
        raise HTTPException(status_code=404, detail="Constellations not found")
    return constellations