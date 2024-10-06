import os

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import exoplanets, stars, constellations, generate_map


if not os.path.exists("data"):
    os.makedirs("data")

# Initialize FastAPI app
app = FastAPI()

# set CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter( prefix="/api", tags=["api"] )

# Include routers from other files
api_router.include_router(exoplanets.router)
api_router.include_router(stars.router)
api_router.include_router(constellations.router)
api_router.include_router(generate_map.router)

# Include API router
app.include_router(api_router)
