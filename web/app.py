from flask import Flask, render_template
import requests, os

app      = Flask(__name__)
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

@app.route("/")
def index():
    try:
        sismos = requests.get(f"{API_BASE}/sismos?limit=15", timeout=5).json()
        stats  = requests.get(f"{API_BASE}/sismos/estadisticas",   timeout=5).json()
    except:
        sismos, stats = [], {}

    return render_template("index.html",
                           sismos=sismos, stats=stats,
                           api_base=API_BASE)
                           
@app.route("/api/geojson")
def geojson_proxy():
    try:
        data = requests.get(f"{API_BASE}/sismos/geojson", timeout=5).json()
        from flask import jsonify
        return jsonify(data)
    except:
        return jsonify({"type": "FeatureCollection", "features": []})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

