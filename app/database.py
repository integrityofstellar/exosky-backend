from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import JSON, Column, Integer, String, create_engine, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./exosky.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Constellation(Base):
    __tablename__ = "constellations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    author = Column(String)
    # list of strings
    stars = Column(JSON)
    planet = Column(String, index=True)


class ConstellationCreate(BaseModel):
    name: str
    author: str
    stars: List[str]
    planet: str


def create_constellation(db: Session, constellation: ConstellationCreate):
    db_constellation = Constellation(
        name=constellation.name,
        author=constellation.author,
        stars=constellation.stars,
        planet=constellation.planet
    )
    db.add(db_constellation)
    db.commit()
    db.refresh(db_constellation)
    return db_constellation

def get_constellations(db: Session) -> List[Constellation]:
    return db.query(Constellation).all()

# get by planet
def get_constellation_by_planet(db: Session, planet: str) -> List[Constellation]:
    return db.query(Constellation).filter(Constellation.planet == planet).all()


Base.metadata.create_all(bind=engine)