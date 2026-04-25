from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal, Sismo, crear_tablas, guardar_sismos
from fetch_sismos import obtener_sismos_con_coords

app = FastAPI(
    title="API Sismos Chile",
    description="Datos del Centro Sismológico Nacional con coordenadas para mapas",
    version="2.0.0",
    root_path="/api",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

crear_tablas()


# ── Helper para serializar un objeto Sismo a dict ───────
def sismo_a_dict(s):
    return {
        "id":             s.id,
        "fecha":          s.fecha,
        "magnitud":       s.magnitud,
        "profundidad_km": s.profundidad_km,
        "referencia":     s.referencia,
        "ciudad":         s.ciudad,
        "lat":            s.lat,
        "lon":            s.lon,
        "clasificacion":  s.clasificacion,
    }


# ── Endpoints ───────────────────────────────────────────

@app.get("/")
def health():
    return {"estado": "online", "api": "Sismos Chile 🌋"}


@app.get("/sismos")
def listar(
    limit:   int   = Query(20,  ge=1,   le=200),
    min_mag: float = Query(0.0, ge=0.0),
):
    db = SessionLocal()
    try:
        rows = db.query(Sismo)\
                 .filter(Sismo.magnitud >= min_mag)\
                 .order_by(Sismo.id.desc()).limit(limit).all()
        return [sismo_a_dict(r) for r in rows]
    finally:
        db.close()


# ⚠️ IMPORTANTE: rutas específicas ANTES de /sismos/{id}
@app.get("/sismos/geojson")
def geojson(min_mag: float = Query(0.0, ge=0.0)):
    db = SessionLocal()
    try:
        sismos = db.query(Sismo)\
                   .filter(Sismo.lat != None, Sismo.magnitud >= min_mag)\
                   .order_by(Sismo.id.desc()).all()
        features = []
        for s in sismos:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type":        "Point",
                    "coordinates": [s.lon, s.lat],
                },
                "properties": {
                    "id":             s.id,
                    "fecha":          s.fecha,
                    "magnitud":       s.magnitud,
                    "profundidad_km": s.profundidad_km,
                    "referencia":     s.referencia,
                    "clasificacion":  s.clasificacion,
                },
            })
        return {"type": "FeatureCollection", "features": features}
    finally:
        db.close()


@app.get("/sismos/estadisticas")
def estadisticas():
    db = SessionLocal()
    try:
        total      = db.query(func.count(Sismo.id)).scalar()
        max_mag    = db.query(func.max(Sismo.magnitud)).scalar()
        avg_mag    = db.query(func.avg(Sismo.magnitud)).scalar()
        avg_prof   = db.query(func.avg(Sismo.profundidad_km)).scalar()
        con_coords = db.query(func.count(Sismo.id))\
                       .filter(Sismo.lat != None).scalar()
        return {
            "total":             total,
            "con_coordenadas":   con_coords,
            "magnitud_maxima":   round(max_mag  or 0, 1),
            "magnitud_promedio": round(avg_mag  or 0, 2),
            "profundidad_prom":  round(avg_prof or 0, 1),
        }
    finally:
        db.close()


@app.get("/sismos/clasificacion/{nivel}")
def por_clasificacion(nivel: str):
    niveles_validos = ["micro", "menor", "ligero", "moderado", "fuerte", "mayor"]
    if nivel not in niveles_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Nivel inválido. Usa uno de: {niveles_validos}"
        )
    db = SessionLocal()
    try:
        rows = db.query(Sismo)\
                 .filter(Sismo.clasificacion == nivel)\
                 .order_by(Sismo.id.desc()).all()
        return [sismo_a_dict(r) for r in rows]
    finally:
        db.close()


# ⚠️ Este va AL FINAL porque {sismo_id} captura cualquier string
@app.get("/sismos/{sismo_id}")
def obtener_sismo(sismo_id: int):
    db = SessionLocal()
    try:
        s = db.query(Sismo).filter(Sismo.id == sismo_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Sismo no encontrado")
        return sismo_a_dict(s)
    finally:
        db.close()


@app.post("/sismos/actualizar")
def actualizar():
    sismos     = obtener_sismos_con_coords()
    insertados = guardar_sismos(sismos)
    return {"consultados": len(sismos), "nuevos": insertados}
