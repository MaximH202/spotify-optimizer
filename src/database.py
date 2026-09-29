import os
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timezone

# URL aus der Docker-Umgebungsvariable holen
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Lokaler Fallback zu SQLite für einfaches Testen ohne Docker
    DATABASE_URL = "sqlite:///spotify_optimizer.db"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def _utcnow():
    # Naiver UTC-Zeitstempel (Spalte ist ohne Zeitzone)
    return datetime.now(timezone.utc).replace(tzinfo=None)

#Modell für die Historie der Optimierungen in der Datenbank
class OptimizationHistory(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(String)
    vibe = Column(String)
    results = Column(JSON)  # Hier speichern wir die added/removed songs
    timestamp = Column(DateTime, default=_utcnow)

# Datenbank initialisieren
def init_db():
    Base.metadata.create_all(bind=engine)

#Optimierung in der Datenbank speichern
def save_optimization(playlist_id, vibe, results):
    db = SessionLocal()
    try:
        new_entry = OptimizationHistory(
            playlist_id=playlist_id,
            vibe=vibe,
            results=results
        )
        db.add(new_entry)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

#Alle Optimierungen aus der Datenbank abrufen (neueste zuerst)
def get_all_optimizations():
    db = SessionLocal()
    try:
        return db.query(OptimizationHistory).order_by(OptimizationHistory.timestamp.desc()).all()
    finally:
        db.close()
