import io
import json
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from app.database import SessionLocal, Constellation
from app.routers.stars import fetch_hipparcos_stars
from app.schemas import Star, ConstellationSchema, StarsResponse
from ..services import fetch_exoplanet_data, fetch_exoplanets_data, celestial_to_xyz, calculate_intensity
from ..utils import get_cached_result, cache_result
from astropy.coordinates import SkyCoord
from astropy import units as u
from astroquery.vizier import Vizier
from ..models import Coordinates

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def fetch_stars(ra: float, dec: float, limiting_magnitude: int = 6) -> List[Star]:
    coords = Coordinates(ra=ra, dec=dec)
    try:
        stars_response = fetch_hipparcos_stars(coords, limiting_magnitude)
        return stars_response.data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching star data: {str(e)}")

def create_star_map(stars: List[Star], constellations: List[ConstellationSchema], show_coordinates: bool = False):
    # Create a black background
    width, height = 3840, 2160  # 4K resolution
    image = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(image)

    # Calculate scaling factors
    ra_values = [star.ra for star in stars]
    dec_values = [star.dec for star in stars]
    
    ra_min, ra_max = min(ra_values), max(ra_values)
    dec_min, dec_max = min(dec_values), max(dec_values)

    # Calculate the range of RA and Dec
    ra_range = ra_max - ra_min
    dec_range = dec_max - dec_min

    # Determine the aspect ratio of the data
    data_aspect_ratio = ra_range / dec_range if dec_range != 0 else 1

    # Determine the aspect ratio of the image
    image_aspect_ratio = width / height

    # Adjust scaling to maintain aspect ratio
    if data_aspect_ratio > image_aspect_ratio:
        x_scale = width / ra_range
        y_scale = x_scale
    else:
        y_scale = height / dec_range
        x_scale = y_scale

    # Calculate padding to center the map
    x_padding = (width - ra_range * x_scale) / 2
    y_padding = (height - dec_range * y_scale) / 2

    # Draw stars
    for star in stars:
        x = int((star.ra - ra_min) * x_scale + x_padding)
        y = int((dec_max - star.dec) * y_scale + y_padding)  # Invert y-axis
        size = max(1, int(5 * (1 - star.phot_g_mean_mag / 20)))  # Adjust star size based on magnitude
        brightness = int(255 * (1 - star.phot_g_mean_mag / 20))  # Adjust star brightness based on magnitude
        draw.ellipse([x-size, y-size, x+size, y+size], fill=(brightness, brightness, brightness))

    # Draw constellations
    for constellation in constellations:
        points = []
        for star_id in constellation.stars:
            star = next((s for s in stars if s.SOURCE_ID == star_id), None)
            if star:
                x = int((star.ra - ra_min) * x_scale + x_padding)
                y = int((dec_max - star.dec) * y_scale + y_padding)  # Invert y-axis
                points.append((x, y))
        
        if len(points) > 1:
            draw.line(points, fill='blue', width=2)

    # Draw coordinates if requested
    if show_coordinates:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
        for i in range(0, width, width//8):
            ra = ra_min + (i - x_padding) / x_scale
            draw.text((i, height-30), f"RA: {ra:.1f}°", fill='white', font=font)
        for i in range(0, height, height//8):
            dec = dec_max - (i - y_padding) / y_scale
            draw.text((10, i), f"Dec: {dec:.1f}°", fill='white', font=font)

    return image

@router.get("/generate_star_map")
async def generate_star_map(
    planet: str,
    show_coordinates: bool = Query(True),
    db: Session = Depends(get_db)
):
    # Fetch exoplanet data
    exoplanet_data = fetch_exoplanet_data(planet)
    if not exoplanet_data:
        raise HTTPException(status_code=404, detail="Exoplanet not found")
    
    # Fetch stars
    stars = fetch_stars(exoplanet_data[0]['ra'], exoplanet_data[0]['dec'])

    # Fetch constellations from the database
    constellations = db.query(Constellation).filter(Constellation.planet == planet).all()
    constellation_schemas = [ConstellationSchema(name=c.name, stars=c.stars, author=c.author) for c in constellations]

    # Generate the star map
    star_map = create_star_map(stars, constellation_schemas, show_coordinates)

    # Convert the image to bytes
    img_byte_arr = io.BytesIO()
    star_map.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    return Response(content=img_byte_arr, media_type="image/png")
