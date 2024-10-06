from fastapi import APIRouter, HTTPException
from app.schemas import StarsResponse, Star
from ..models import Coordinates
from ..services import celestial_to_xyz, calculate_intensity
from ..utils import get_cached_result, cache_result
import json
from astropy.coordinates import SkyCoord
from astropy import units as u
from astroquery.vizier import Vizier
import numpy as np

router = APIRouter()

@router.post("/stars/", response_model=StarsResponse)
def fetch_hipparcos_stars(coords: Coordinates, limiting_magnitude: int = 6, force_skip_cache: bool = False):
    """
    Fetch visible stars around a given set of coordinates from the Hipparcos catalog.
    Coordinates (coords): Right ascension and declination of the exoplanet.
    Limiting magnitude (limiting_magnitude): Stars brighter than this magnitude.
    """
    try:
        # Caching mechanism
        cache_key = f"stars_{coords.ra}_{coords.dec}_{limiting_magnitude}"
        cached_result = get_cached_result(cache_key)
        if cached_result and not force_skip_cache:
            data = json.loads(cached_result)
            return StarsResponse(
                data=[Star(**item) for item in data["data"]],
                metadata={"total": len(data["data"])}
            )

        # Query Hipparcos catalog
        exoplanet = SkyCoord(ra=coords.ra, dec=coords.dec, unit=(u.degree, u.degree))
        v = Vizier(column_filters={"Vmag": f"<{limiting_magnitude}"}, row_limit=-1)
        catalog = v.get_catalogs("I/239/hip_main")[0]

        # Ensure necessary columns exist
        required_columns = ['RAICRS', 'DEICRS', 'Plx', 'Vmag', 'HIP']
        for col in required_columns:
            if col not in catalog.colnames:
                raise ValueError(f"Missing required column: {col}")

        # Conversion to Cartesian coordinates and intensity calculation
        def convert_to_xyz_and_intensity(ra, dec, parallax, magnitude):
            try:
                distance = 1 / parallax if parallax != 0 else 1  # Default distance to 1 if parallax is 0
                x, y, z = celestial_to_xyz(ra, dec, distance)
                intensity = calculate_intensity(magnitude, distance)
                return x, y, z, intensity
            except Exception as e:
                print(f"Error in conversion: {e}")
                return None, None, None, None


        processed_results = []
        for item in catalog:
            try:
                ra = np.ma.getdata(item['RAICRS']) if not np.ma.is_masked(item['RAICRS']) else None
                dec = np.ma.getdata(item['DEICRS']) if not np.ma.is_masked(item['DEICRS']) else None
                parallax = np.ma.getdata(item['Plx']) if not np.ma.is_masked(item['Plx']) else None
                magnitude = np.ma.getdata(item['Vmag']) if not np.ma.is_masked(item['Vmag']) else None

                # Convert to standard Python types, handling any issues
                ra = float(ra) if ra is not None and not np.isnan(ra) else None
                dec = float(dec) if dec is not None and not np.isnan(dec) else None
                parallax = float(parallax) if parallax is not None and not np.isnan(parallax) else None
                magnitude = float(magnitude) if magnitude is not None and not np.isnan(magnitude) else None

                if ra is not None and dec is not None and parallax is not None and magnitude is not None:
                    x, y, z, intensity = convert_to_xyz_and_intensity(ra, dec, parallax, magnitude)
                    if x is not None:
                        _item = {
                            'SOURCE_ID': int(item['HIP']) if item['HIP'] is not None and not np.isnan(item['HIP']) else None,
                            'ra': ra,
                            'dec': dec,
                            'phot_g_mean_mag': magnitude,
                            'parallax': parallax,
                            'x': x,
                            'y': y,
                            'z': z,
                            'intensity': intensity
                        }
                        processed_results.append(_item)
            except Exception as e:
                print(f"Error converting star data: {e}")

        # Clean the results by removing invalid values (NaN, Inf, etc.)
        cleaned_results = [
            {k: (v if isinstance(v, (int, float, str)) and not (v != v or v == float('inf') or v == -float('inf')) else None) for k, v in item.items()}
            for item in processed_results
        ]

        # Cache the results for future requests
        cache_result(cache_key, json.dumps({"data": cleaned_results}))

        return StarsResponse(
            data=[Star(**item) for item in cleaned_results],
            metadata={"total": len(cleaned_results)}
        )

    except Exception as e:
        # Log any errors and return HTTP 500
        raise HTTPException(status_code=500, detail=f"Error fetching star data: {e}")
