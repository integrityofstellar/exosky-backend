from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    EXOPLANETS_URL: AnyHttpUrl = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"



config = Config()
