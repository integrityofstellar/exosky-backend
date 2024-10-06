import numpy as np
from .config import config
import requests

def celestial_to_xyz(ra, dec, distance):
    ra_rad = np.deg2rad(ra)
    dec_rad = np.deg2rad(dec)
    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)
    return x, y, z

def calculate_intensity(magnitude, distance):
    luminosity = 10 ** (0 - magnitude / 2.5)
    intensity = luminosity / (distance ** 2) if distance > 0 else 0
    return intensity

def fetch_exoplanets_data():
    response = requests.post(config.EXOPLANETS_URL, data={"query": "SELECT pl_name, ra, dec, sy_dist FROM pscomppars", "format": "json"})
    response.raise_for_status()
    return response.json()

def fetch_exoplanet_data(planet):
    response = requests.post(config.EXOPLANETS_URL, data={"query": f"SELECT pl_name, ra, dec, sy_dist FROM pscomppars WHERE pl_name = '{planet}'", "format": "json"})
    response.raise_for_status()
    return response.json()