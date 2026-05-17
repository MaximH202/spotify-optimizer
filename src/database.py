import os
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# URL aus der Docker-Umgebungsvariable holen
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/spotify_optimizer")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#Modell für die Historie der Optimierungen in der Datenbank
class OptimizationHistory(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(String)
    vibe = Column(String)
    results = Column(JSON)  # Hier speichern wir die added/removed songs
    timestamp = Column(DateTime, default=datetime.utcnow)

# Datenbank initialisieren
def init_db():
    Base.metadata.create_all(bind=engine)

#Optimierung in der Datenbank speichern
def save_optimization(playlist_id, vibe, results):
    db = SessionLocal()
    new_entry = OptimizationHistory(
        playlist_id=playlist_id,
        vibe=vibe,
        results=results
    )
    db.add(new_entry)
    db.commit()
    db.close()

#Alle Optimierungen aus der Datenbank abrufen
def get_all_optimizations():
    db = SessionLocal()
    optimizations = db.query(OptimizationHistory).all()
    db.close()
    return optimizations