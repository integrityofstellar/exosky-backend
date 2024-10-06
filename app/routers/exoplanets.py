import os
import requests
from fastapi import APIRouter, Query, HTTPException

from app.schemas import ExoplanetsResponse
from ..services import fetch_exoplanets_data, celestial_to_xyz
import json

router = APIRouter()

@router.get("/exoplanets/", response_model=ExoplanetsResponse)
def fetch_exoplanets(use_local_dataset: bool = True, limit: int = Query(20, le=7000), offset: int = Query(0, ge=0)):
    try:
        if use_local_dataset and os.path.exists("data/exoplanets.json"):
            with open("data/exoplanets.json", "r") as f:
                data = json.load(f)
        else:
            data = fetch_exoplanets_data()
            if not os.path.exists("data/exoplanets.json"):
                with open("data/exoplanets.json", "w") as f:
                    json.dump(data, f)

        paginated_data = data[offset:offset + limit]
        for item in paginated_data:
            item['x'], item['y'], item['z'] = celestial_to_xyz(item['ra'], item['dec'], item['sy_dist'] if item['sy_dist'] else 0)

        return {
            "data": paginated_data,
            "metadata": {
                "limit": limit,
                "offset": offset,
                "total": len(data),
                "has_next": offset + limit < len(data),
                "has_prev": offset > 0
            }
        }
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching exoplanet data: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
