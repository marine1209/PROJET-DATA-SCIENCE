import requests
import pandas as pd


dfs_meteo = []
points_france = [
    {"name": "Paris",        "lat": 48.85, "lon": 2.35},
    {"name": "Lyon",         "lat": 45.75, "lon": 4.85},
    {"name": "Marseille",    "lat": 43.30, "lon": 5.37},
    {"name": "Bordeaux",     "lat": 44.84, "lon": -0.58},
    {"name": "Toulouse",     "lat": 43.60, "lon": 1.44},
    {"name": "Strasbourg",   "lat": 48.57, "lon": 7.75},
    {"name": "Nantes",       "lat": 47.22, "lon": -1.55},
    {"name": "Montpellier",  "lat": 43.61, "lon": 3.87},
    {"name": "Nice",         "lat": 43.71, "lon": 7.26},
    {"name": "Rennes",       "lat": 48.11, "lon": -1.68},
    {"name": "Clermont",     "lat": 45.78, "lon": 3.08},
    {"name": "Limoges",      "lat": 45.83, "lon": 1.26},
]

for point in points_france:
    print(f"Téléchargement {point['name']}...")
    url = (
    f"https://archive-api.open-meteo.com/v1/archive"
    f"?latitude={point['lat']}&longitude={point['lon']}"
    f"&start_date=2019-01-01"
    f"&end_date=2025-12-31"
    f"&hourly=shortwave_radiation,temperature_2m"  # ← retour à hourly
    f"&timezone=Europe%2FParis"
)
    response = requests.get(url)
    data = response.json()
    print(data.keys())
    print(data)
    df = pd.DataFrame({
    "timestamp":        pd.to_datetime(data["hourly"]["time"]),  # ← hourly
    "rayonnement_reel": data["hourly"]["shortwave_radiation"],
    "temperature":      data["hourly"]["temperature_2m"],
    "ville":            point["name"]
})
    dfs_meteo.append(df)

# Moyenne nationale par timestamp
df_meteo_raw = pd.concat(dfs_meteo, ignore_index=True)
df_meteo_national = df_meteo_raw.groupby("timestamp").agg(
    rayonnement_reel = ("rayonnement_reel", "mean"),
    temperature      = ("temperature",      "mean")
).reset_index()

print(f"✓ {len(df_meteo_national)} mesures | {df_meteo_national['timestamp'].min()} → {df_meteo_national['timestamp'].max()}")
print(df_meteo_national.head())

# Sauvegarder pour ne pas re-télécharger à chaque fois
df_meteo_national.to_csv("data/meteo_openmeteo_2019_2025.csv", index=False)
print("✓ Sauvegardé dans data/meteo_openmeteo_2019_2025.csv")