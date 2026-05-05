"""
Biomass Grinding Energy Simulation - Backend API
Based on: "Energy Consumption at Size Reduction of Lignocellulose Biomass for Bioenergy"
Sustainability 2019, 11, 2477
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error

app = FastAPI(
    title="Biomass Grinding Energy Simulation API",
    description="ML-powered simulation of energy consumption in lignocellulosic biomass size reduction",
    version="1.0.0"
)

# ============================================================
# EXPERIMENTAL DATA (directly from paper)
# ============================================================

# Knife Mill GM200 - Table 1
KNIFE_SPEEDS = [3000, 4500, 6000, 7500, 9000]  # rpm

KNIFE_DATA = {
    "alfalfa": {
        "mean_power":  [480, 460, 420, 410, 410],   # Watts
        "max_power":   [610, 620, 625, 630, 640],   # Watts
        "sec":         [1.44, 1.38, 1.26, 1.23, 1.23],  # MJ/kg
    },
    "corn_stalk": {
        "mean_power":  [770, 560, 480, 420, 390],
        "max_power":   [1850, 1900, 2000, 2150, 2200],
        "sec":         [2.31, 1.68, 1.44, 1.26, 1.17],
    },
    "mountain_grass": {
        "mean_power":  [480, 440, 420, 420, 410],
        "max_power":   [580, 600, 650, 670, 690],
        "sec":         [1.44, 1.32, 1.26, 1.26, 1.23],
    },
}

# Granulometric Analysis - Table 2
SIEVE_SIZES = [0.00, 0.71, 1.00, 1.40, 2.00, 2.80]  # mm orifice

GRANULO_DATA = {
    "alfalfa": {
        "distributions": [
            [7.5, 3.0, 2.5, 1.0, 22.5, 63.5],
            [23.0, 13.0, 9.0, 1.5, 26.5, 27.0],
            [46.0, 22.5, 11.5, 3.0, 15.0, 2.0],
            [53.0, 25.5, 14.0, 2.5, 5.0, 0.0],
            [58.5, 28.0, 12.5, 0.5, 0.5, 0.0],
        ],
        "mean_size": [2.80, 1.88, 0.97, 0.74, 0.62],  # mm
    },
    "corn_stalk": {
        "distributions": [
            [4.5, 1.5, 1.5, 0.5, 8.0, 84.0],
            [15.0, 6.5, 5.5, 1.0, 12.5, 59.5],
            [28.5, 14.0, 9.0, 1.5, 18.0, 29.0],
            [38.0, 19.5, 10.5, 1.5, 20.0, 10.5],
            [40.5, 20.5, 12.0, 2.0, 21.0, 4.0],
        ],
        "mean_size": [3.10, 2.51, 1.77, 1.29, 1.14],
    },
    "mountain_grass": {
        "distributions": [
            [8.0, 6.0, 5.5, 1.5, 19.5, 59.5],
            [16.0, 11.5, 6.5, 1.5, 22.0, 42.5],
            [21.5, 12.5, 7.0, 2.5, 20.5, 36.0],
            [41.0, 23.0, 9.5, 2.5, 20.5, 3.5],
            [54.0, 25.0, 13.5, 3.5, 4.0, 0.0],
        ],
        "mean_size": [2.66, 2.23, 2.03, 1.11, 0.72],
    },
}

# Hammer Mill MC-22 (22kW) - Approximate from Figures 6 & 7
HAMMER_SPEEDS = [400, 600, 800, 1000, 1200, 1500]  # rpm

HAMMER_DATA = {
    "miscanthus": {
        "16mm": [24.5, 21.5, 19.0, 17.0, 15.5, 14.2],  # kWh/t
        "10mm": [32.0, 28.5, 25.0, 21.5, 18.5, 16.0],
    },
    "willow": {
        "16mm": [16.0, 14.5, 13.0, 11.8, 11.0, 10.2],
        "10mm": [22.0, 19.5, 17.0, 14.8, 13.0, 11.5],
    },
}

# ============================================================
# ML MODEL TRAINING
# ============================================================

KNIFE_BIOMASS_TYPES  = list(KNIFE_DATA.keys())
HAMMER_BIOMASS_TYPES = list(HAMMER_DATA.keys())

def build_poly_model(degree=2, alpha=0.01):
    return Pipeline([
        ("poly", PolynomialFeatures(degree=degree, include_bias=True)),
        ("reg", Ridge(alpha=alpha)),
    ])

def per_biomass_metrics(model_dict, X_speed, data_dict, key):
    all_actual, all_pred = [], []
    for b, m in model_dict.items():
        actual = data_dict[b][key]
        pred   = m.predict(X_speed).tolist()
        all_actual.extend(actual)
        all_pred.extend(pred)
    r2  = round(r2_score(all_actual, all_pred), 4)
    mae = round(mean_absolute_error(all_actual, all_pred), 4)
    return {"r2": r2, "mae": mae}

def train_all_models():
    X_speed = np.array(KNIFE_SPEEDS).reshape(-1, 1)

    # --- Per-biomass knife mill models ---
    knife_energy_models   = {}
    knife_power_models    = {}
    knife_particle_models = {}

    for biomass in KNIFE_BIOMASS_TYPES:
        y_e = np.array(KNIFE_DATA[biomass]["sec"])
        y_p = np.array(KNIFE_DATA[biomass]["mean_power"])
        y_s = np.array(GRANULO_DATA[biomass]["mean_size"])

        knife_energy_models[biomass]   = build_poly_model(2, 0.01).fit(X_speed, y_e)
        knife_power_models[biomass]    = build_poly_model(2, 0.01).fit(X_speed, y_p)
        knife_particle_models[biomass] = build_poly_model(2, 0.01).fit(X_speed, y_s)

    # --- Per-biomass per-sieve hammer mill models ---
    hammer_energy_models = {}
    X_hspeed = np.array(HAMMER_SPEEDS).reshape(-1, 1)

    for biomass in HAMMER_BIOMASS_TYPES:
        hammer_energy_models[biomass] = {}
        for sieve in ["10mm", "16mm"]:
            y_h = np.array(HAMMER_DATA[biomass][sieve])
            hammer_energy_models[biomass][sieve] = build_poly_model(2, 0.01).fit(X_hspeed, y_h)

    # Aggregate metrics
    km_e_metrics = per_biomass_metrics(knife_energy_models,   X_speed,  KNIFE_DATA,    "sec")
    km_p_metrics = per_biomass_metrics(knife_power_models,    X_speed,  KNIFE_DATA,    "mean_power")
    km_s_metrics = per_biomass_metrics(knife_particle_models, X_speed,  GRANULO_DATA,  "mean_size")

    all_h_actual, all_h_pred = [], []
    for b in HAMMER_BIOMASS_TYPES:
        for sieve in ["10mm", "16mm"]:
            actual = HAMMER_DATA[b][sieve]
            pred   = hammer_energy_models[b][sieve].predict(X_hspeed).tolist()
            all_h_actual.extend(actual); all_h_pred.extend(pred)
    hm_metrics = {"r2": round(r2_score(all_h_actual, all_h_pred), 4),
                  "mae": round(mean_absolute_error(all_h_actual, all_h_pred), 4)}

    print("=== ML Model Training Complete ===")
    print(f"  Knife Energy   R²={km_e_metrics['r2']}")
    print(f"  Knife Power    R²={km_p_metrics['r2']}")
    print(f"  Knife Particle R²={km_s_metrics['r2']}")
    print(f"  Hammer Energy  R²={hm_metrics['r2']}")

    return {
        "knife_energy":   (knife_energy_models,   km_e_metrics),
        "knife_power":    (knife_power_models,     km_p_metrics),
        "knife_particle": (knife_particle_models,  km_s_metrics),
        "hammer_energy":  (hammer_energy_models,   hm_metrics),
    }

MODELS = train_all_models()

def predict_knife(biomass, speed):
    X = np.array([[speed]])
    energy   = float(MODELS["knife_energy"][0][biomass].predict(X)[0])
    power    = float(MODELS["knife_power"][0][biomass].predict(X)[0])
    particle = float(MODELS["knife_particle"][0][biomass].predict(X)[0])
    return max(0.5, energy), max(50.0, power), max(0.1, particle)

def predict_hammer(biomass, speed, sieve):
    X = np.array([[speed]])
    energy = float(MODELS["hammer_energy"][0][biomass][sieve].predict(X)[0])
    return max(5.0, energy)

# ============================================================
# REQUEST SCHEMAS
# ============================================================

class KnifeRequest(BaseModel):
    biomass_type: str   # alfalfa | corn_stalk | mountain_grass
    speed: float        # rpm 2000–10000

class HammerRequest(BaseModel):
    biomass_type: str   # miscanthus | willow
    speed: float        # rpm 300–2000
    sieve_size: str     # 10mm | 16mm

class OptimizeRequest(BaseModel):
    biomass_type: str
    mill_type: str      # knife | hammer
    target_particle_size: Optional[float] = None  # mm (knife only)
    sieve_size: Optional[str] = "10mm"            # hammer only

# ============================================================
# ROUTES
# ============================================================

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api/health")
async def health():
    return {"status": "running", "models": list(MODELS.keys())}

@app.get("/api/experimental-data")
async def experimental_data():
    return {
        "knife": {
            "speeds": KNIFE_SPEEDS,
            "biomass": KNIFE_DATA,
        },
        "granulometric": {
            "sieve_sizes": SIEVE_SIZES,
            "speeds": KNIFE_SPEEDS,
            "biomass": GRANULO_DATA,
        },
        "hammer": {
            "speeds": HAMMER_SPEEDS,
            "biomass": HAMMER_DATA,
        },
    }

@app.post("/api/predict/knife-mill")
async def api_predict_knife(req: KnifeRequest):
    if req.biomass_type not in KNIFE_BIOMASS_TYPES:
        raise HTTPException(400, f"biomass_type must be one of {KNIFE_BIOMASS_TYPES}")
    if not 2000 <= req.speed <= 10000:
        raise HTTPException(400, "speed must be 2000–10000 rpm for knife mill")

    energy, power, particle = predict_knife(req.biomass_type, req.speed)

    return {
        "biomass_type": req.biomass_type,
        "speed_rpm": req.speed,
        "predictions": {
            "specific_energy_mj_per_kg":   round(energy, 4),
            "specific_energy_kwh_per_ton": round(energy * 1000 / 3.6, 2),
            "mean_power_watts":            round(power, 1),
            "mean_particle_size_mm":       round(particle, 3),
        },
        "model_metrics": {
            "energy_r2":   MODELS["knife_energy"][1]["r2"],
            "power_r2":    MODELS["knife_power"][1]["r2"],
            "particle_r2": MODELS["knife_particle"][1]["r2"],
        },
    }

@app.post("/api/predict/hammer-mill")
async def api_predict_hammer(req: HammerRequest):
    if req.biomass_type not in HAMMER_BIOMASS_TYPES:
        raise HTTPException(400, f"biomass_type must be one of {HAMMER_BIOMASS_TYPES}")
    if req.sieve_size not in ["10mm", "16mm"]:
        raise HTTPException(400, "sieve_size must be '10mm' or '16mm'")
    if not 300 <= req.speed <= 2000:
        raise HTTPException(400, "speed must be 300–2000 rpm for hammer mill")

    energy = predict_hammer(req.biomass_type, req.speed, req.sieve_size)
    sieve_mm = int(req.sieve_size.replace("mm", ""))

    return {
        "biomass_type": req.biomass_type,
        "speed_rpm": req.speed,
        "sieve_size": req.sieve_size,
        "predictions": {
            "specific_energy_kwh_per_ton": round(energy, 2),
            "specific_energy_mj_per_kg":   round(energy * 3.6 / 1000, 4),
            "cost_per_ton_usd":            round(energy * 0.10, 2),
            "cost_per_kg_usd":             round(energy * 0.10 / 1000, 4),
            "max_output_particle_mm":      round(sieve_mm * 0.65, 1),
        },
        "model_metrics": {
            "r2":  MODELS["hammer_energy"][1]["r2"],
            "mae": MODELS["hammer_energy"][1]["mae"],
        },
    }

@app.post("/api/optimize")
async def optimize(req: OptimizeRequest):
    results = []

    if req.mill_type == "knife":
        if req.biomass_type not in KNIFE_BIOMASS_TYPES:
            raise HTTPException(400, "Invalid biomass type for knife mill")
        for speed in np.arange(3000, 9001, 100):
            energy, power, particle = predict_knife(req.biomass_type, float(speed))
            score = energy
            if req.target_particle_size:
                score += abs(particle - req.target_particle_size) * 0.5
            results.append({"speed": float(speed), "energy": round(energy, 4),
                            "particle_size": round(particle, 3), "power": round(power, 1),
                            "score": round(score, 4)})
        optimal = min(results, key=lambda r: r["score"])
        return {"mill_type": "knife", "biomass_type": req.biomass_type,
                "optimal": optimal, "sweep": results[::6]}

    elif req.mill_type == "hammer":
        if req.biomass_type not in HAMMER_BIOMASS_TYPES:
            raise HTTPException(400, "Invalid biomass type for hammer mill")
        sieve = req.sieve_size or "10mm"
        for speed in np.arange(400, 1501, 50):
            energy = predict_hammer(req.biomass_type, float(speed), sieve)
            results.append({"speed": float(speed), "energy": round(energy, 2)})
        optimal = min(results, key=lambda r: r["energy"])
        return {"mill_type": "hammer", "biomass_type": req.biomass_type,
                "sieve_size": sieve, "optimal": optimal, "sweep": results}

    else:
        raise HTTPException(400, "mill_type must be 'knife' or 'hammer'")

@app.get("/api/model-metrics")
async def model_metrics():
    return {
        "knife_energy":   {**MODELS["knife_energy"][1],   "description": "Specific Energy (MJ/kg)"},
        "knife_power":    {**MODELS["knife_power"][1],    "description": "Mean Power (W)"},
        "knife_particle": {**MODELS["knife_particle"][1], "description": "Mean Particle Size (mm)"},
        "hammer_energy":  {**MODELS["hammer_energy"][1],  "description": "Specific Energy (kWh/t)"},
    }

@app.get("/api/sweep/knife/{biomass_type}")
async def knife_sweep(biomass_type: str):
    if biomass_type not in KNIFE_BIOMASS_TYPES:
        raise HTTPException(400, "Invalid biomass type")
    speeds = list(range(2500, 10001, 250))
    result = {"speeds": speeds, "energy": [], "power": [], "particle": []}
    for speed in speeds:
        e, p, s = predict_knife(biomass_type, float(speed))
        result["energy"].append(round(e, 4))
        result["power"].append(round(p, 1))
        result["particle"].append(round(s, 3))
    return result

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False)
