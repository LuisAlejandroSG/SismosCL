import re
import time
import json
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

API_URL   = "https://api.gael.cloud/general/public/sismos"
geocoder  = Nominatim(user_agent="sismos-actividad4-ipvg")
PATRON_CIUDAD = re.compile(r'\bde\s+(.+)$', re.IGNORECASE)


def extraer_ciudad(ref: str) -> str:
    m = PATRON_CIUDAD.search(ref.strip())
    return m.group(1).strip() if m else ref.strip()


def geocodificar(ciudad: str) -> tuple[float, float] | None:
    for query in [f"{ciudad}, Chile", ciudad]:
        try:
            loc = geocoder.geocode(query, timeout=8)
            if loc:
                return loc.latitude, loc.longitude
        except GeocoderTimedOut:
            time.sleep(2)
        time.sleep(1.1)  
    return None


def clasificar_magnitud(m: float) -> str:
    if   m < 2.0: return "micro"
    elif m < 4.0: return "menor"
    elif m < 5.0: return "ligero"
    elif m < 6.0: return "moderado"
    elif m < 7.0: return "fuerte"
    else:          return "mayor"


def obtener_sismos_con_coords() -> list[dict]:
    resp = requests.get(API_URL, timeout=10)
    resp.raise_for_status()
    raw  = resp.json()

    sismos = []
    for item in raw:
        ciudad = extraer_ciudad(item["RefGeografica"])
        coords = geocodificar(ciudad)

        sismos.append({
            "fecha":         item["Fecha"],
            "magnitud":      float(item["Magnitud"]),
            "profundidad_km":int(item["Profundidad"]),
            "referencia":    item["RefGeografica"],
            "ciudad":        ciudad,
            "lat":           coords[0] if coords else None,
            "lon":           coords[1] if coords else None,
            "clasificacion": clasificar_magnitud(float(item["Magnitud"])),
        })

    return sismos


if __name__ == "__main__":
    print("Obteniendo sismos y geocodificando (puede tardar ~20s)...")
    sismos = obtener_sismos_con_coords()
    for s in sismos:
        coord_str = f"({s['lat']:.2f}, {s['lon']:.2f})" if s['lat'] else "sin coords"
        print(f"  M{s['magnitud']} {s['referencia']:45} → {coord_str}")