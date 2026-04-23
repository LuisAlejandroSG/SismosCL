from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine       = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()


class Sismo(Base):
    __tablename__ = "sismos"

    id             = Column(Integer, primary_key=True, index=True)
    fecha          = Column(String(30),  nullable=False)
    magnitud       = Column(Float,        nullable=False)
    profundidad_km = Column(Integer)
    referencia     = Column(Text)
    ciudad         = Column(String(120))
    lat            = Column(Float,   nullable=True) 
    lon            = Column(Float,   nullable=True) 
    clasificacion  = Column(String(20))
    registrado_en  = Column(DateTime, default=datetime.utcnow)


def crear_tablas():
    Base.metadata.create_all(bind=engine)


def guardar_sismos(lista: list[dict]) -> int:
    db     = SessionLocal()
    nuevos = 0
    try:
        for s in lista:
            existe = db.query(Sismo).filter(
                Sismo.fecha      == s["fecha"],
                Sismo.magnitud   == s["magnitud"],
                Sismo.referencia == s["referencia"],
            ).first()
            if not existe:
                db.add(Sismo(
                    fecha          = s["fecha"],
                    magnitud       = s["magnitud"],
                    profundidad_km = s["profundidad_km"],
                    referencia     = s["referencia"],
                    ciudad         = s["ciudad"],
                    lat            = s.get("lat"),
                    lon            = s.get("lon"),
                    clasificacion  = s["clasificacion"],
                ))
                nuevos += 1
        db.commit()
        return nuevos
    except Exception as e:
        db.rollback(); raise e
    finally:
        db.close()


if __name__ == "__main__":
    from fetch_sismos import obtener_sismos_con_coords
    crear_tablas()
    print("Tabla creada. Obteniendo sismos...")
    sismos = obtener_sismos_con_coords()
    n = guardar_sismos(sismos)
    print(f"✓ {n} sismos guardados con coordenadas.")