# BiomassML — Grinding Energy Simulation

**ECE Major Project | Suhani Tyagi & Vaishali Kasotiya**
**Supervisor: Mr. Sandeep Kumar | February 2026**

---

## Project Overview

This is an **interactive ML-powered simulation** of energy consumption during the mechanical size reduction (grinding) of lignocellulosic biomass — built to visualize and predict findings from the research paper:

> *"Energy Consumption at Size Reduction of Lignocellulose Biomass for Bioenergy"*
> Moiceanu et al., Sustainability 2019, 11, 2477

The simulation lets you:
- **Predict** energy consumption for different biomass types and mill speeds using ML models
- **Visualize** all experimental data from the paper as interactive charts
- **Analyze** granulometric (particle size) distributions
- **Optimize** mill parameters to minimize energy consumption

---

## What is the Research About?

Lignocellulosic biomass (crop residues, energy crops) must be ground to small particle sizes before being converted into biofuels (bioethanol, biogas) or pellets. This grinding step consumes significant energy — often 50–65 kJ/kg — and increases processing costs.

The paper experimentally measures energy consumption for grinding:

| Biomass         | Mill Type   | Speed Range           | Key Finding                     |
|----------------|-------------|----------------------|----------------------------------|
| Alfalfa         | Knife (GM200) | 3000–9000 rpm      | 1.23–1.44 MJ/kg                 |
| Corn Stalk      | Knife (GM200) | 3000–9000 rpm      | 1.17–2.31 MJ/kg (highest)       |
| Mountain Grass  | Knife (GM200) | 3000–9000 rpm      | 1.23–1.44 MJ/kg                 |
| Miscanthus      | Hammer (MC-22)| Industrial speeds  | 14–18 kWh/t (10 mm sieve)      |
| Willow          | Hammer (MC-22)| Industrial speeds  | 10–14 kWh/t (10 mm sieve)      |

**Key insight:** As mill speed increases, specific energy consumption decreases, but particle size also decreases (finer grinding). Corn stalks require the highest energy due to their thick outer wall and large diameter.

---

## Application Features

### 1. Dashboard
Landing page with project overview, key stats, research workflow, and a summary energy comparison chart.

### 2. ML Predictor
Two prediction panels:
- **Knife Mill Predictor**: Enter biomass type + rotor speed → get predicted specific energy (MJ/kg), mean power (W), and output particle size (mm)
- **Hammer Mill Predictor**: Enter biomass type + speed + sieve size → get predicted energy (kWh/t) and cost estimate

### 3. Visualizations
Interactive charts of all experimental data:
- Specific energy vs. rotor speed (all biomass types)
- Mean and max power vs. rotor speed
- Mean particle size vs. rotor speed
- Hammer mill energy: Miscanthus vs. Willow (10mm or 16mm sieve)

### 4. Granulometric Analysis
Select biomass type and speed → see a bar chart showing percentage of material retained on each ISO 3310 classifier sieve (0–2.8 mm orifice range), plus mean particle size statistics.

### 5. Optimization
AI-powered optimization that sweeps rotor speeds and finds the **optimal RPM** that minimizes energy consumption. Optional: constrain by target output particle size.

### 6. ML Metrics
Model accuracy dashboard showing R² scores and Mean Absolute Error for all 4 trained models, plus a Predicted vs. Actual scatter plot and model architecture diagram.

---

## Machine Learning Models

All models use **Polynomial Regression (degree 2)** with Ridge (L2) regularization, trained on the experimental data from the paper.

| Model | Input Features | Output | R² Score |
|-------|---------------|--------|----------|
| Knife Energy | Biomass type (encoded), Rotor speed (rpm) | Specific Energy (MJ/kg) | >0.96 |
| Knife Power  | Biomass type (encoded), Rotor speed (rpm) | Mean Power (W)          | >0.96 |
| Knife Particle | Biomass type (encoded), Rotor speed (rpm) | Mean Particle Size (mm) | >0.97 |
| Hammer Energy | Biomass type (encoded), Speed (rpm), Sieve (mm) | Energy (kWh/t) | >0.98 |

### Why Polynomial Regression?
- The energy-vs-speed relationship follows a **power-type distribution** (R² > 0.969, as stated in the paper)
- Polynomial degree 2 captures this nonlinear behavior
- Ridge regularization prevents overfitting on the small dataset (15–24 data points)

### Feature Engineering
```
Biomass Type  →  Label encoded (alfalfa=0, corn_stalk=1, mountain_grass=2)
Rotor Speed   →  Continuous (rpm)
               ↓
         PolynomialFeatures(degree=2)
               ↓
   [biomass, speed, biomass², biomass×speed, speed²]
               ↓
         Ridge Regression
               ↓
      Prediction (energy / power / particle size)
```

---

## Tech Stack

| Layer     | Technology                            |
|-----------|---------------------------------------|
| Backend   | Python · FastAPI · Uvicorn            |
| ML        | scikit-learn (Polynomial + Ridge)     |
| Frontend  | Vanilla HTML/CSS/JavaScript           |
| Charts    | Chart.js 4.4                          |
| Fonts     | Inter · JetBrains Mono (Google Fonts) |

---

## Project Structure

```
major project/
├── app.py              ← FastAPI backend + ML models
├── requirements.txt    ← Python dependencies
├── start.bat           ← One-click startup script
├── README.md           ← This file
└── static/
    ├── index.html      ← Single-page frontend
    ├── style.css       ← Dark green theme styling
    └── app.js          ← Charts, API calls, UI logic
```

---

## How to Run

### Option A — Double-click (Windows)
```
Double-click start.bat
```
The browser opens automatically at http://localhost:8000

### Option B — Command Line
```bash
# Install dependencies (only needed once)
pip install -r requirements.txt

# Start server
python app.py
```
Then open http://localhost:8000 in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve frontend |
| GET | `/api/health` | System status |
| GET | `/api/experimental-data` | All raw experimental data (JSON) |
| POST | `/api/predict/knife-mill` | Knife mill energy prediction |
| POST | `/api/predict/hammer-mill` | Hammer mill energy prediction |
| POST | `/api/optimize` | Parameter optimization |
| GET | `/api/model-metrics` | ML model accuracy |
| GET | `/api/sweep/knife/{biomass}` | Full speed sweep data |

### Example API Call
```bash
curl -X POST http://localhost:8000/api/predict/knife-mill \
  -H "Content-Type: application/json" \
  -d '{"biomass_type": "corn_stalk", "speed": 6000}'
```

Response:
```json
{
  "biomass_type": "corn_stalk",
  "speed_rpm": 6000,
  "predictions": {
    "specific_energy_mj_per_kg": 1.44,
    "specific_energy_kwh_per_ton": 400.0,
    "mean_power_watts": 480.0,
    "mean_particle_size_mm": 1.77
  },
  "model_metrics": {
    "energy_r2": 0.9623,
    "power_r2": 0.9641,
    "particle_r2": 0.9712
  }
}
```

---

## Reference

Moiceanu, G.; Paraschiv, G.; Voicu, G.; Dinca, M.; Negoita, O.; Chitoiu, M.; Tudor, P.
**Energy Consumption at Size Reduction of Lignocellulose Biomass for Bioenergy.**
*Sustainability* 2019, 11, 2477.
https://doi.org/10.3390/su11092477
