import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import cross_val_score, KFold

def donnees_meteo():
    donnees_meteo = {
        "temperature": {}, 
        "rayonnement": {}, 
        "vent":        {}, 
        "timestamp":   {}
    }
    annees = [2021, 2022, 2023]
    for annee in annees:
        df = pd.read_csv(f"data/donnees-de-temperature-et-de-pseudo-rayonnement_{annee}.csv", sep=";")
        df = df.iloc[::2].reset_index(drop=True)
        df["timestamp"] = pd.to_datetime(df["Horodate"], utc=True).dt.tz_convert("Europe/Paris").dt.tz_localize(None)
        donnees_meteo["temperature"][annee] = df["Température réalisée lissée (°C)"]
        donnees_meteo["rayonnement"][annee]  = df["Pseudo rayonnement (%)"]
        donnees_meteo["timestamp"][annee]    = df["timestamp"]
    return donnees_meteo

def donnees_prod():
    donnees_prod = {
        "eolien":    {},
        "pv":        {},
        "hydro":     {},
        "timestamp": {}
    }
    annees = [2021, 2022, 2023]
    for annee in annees:
        df = pd.read_csv(
            f"Data/eCO2mix prod/eCO2mix_RTE_Annuel-Definitif_{annee}.xls",
            sep="\t",
            encoding="latin-1",
            low_memory=False,
            index_col=False
        )
        df = df[df["Heures"].astype(str).str.match(r"^\d{2}:(00|30)$")].reset_index(drop=True)
        df["timestamp"] = pd.to_datetime(
            df["Date"].astype(str).str.strip() + " " + df["Heures"].astype(str).str.strip(),
            errors="coerce"
        )
        df = df.dropna(subset=["timestamp"]).reset_index(drop=True)
        print(f"{annee} : {len(df)} lignes | {df['timestamp'].min()} → {df['timestamp'].max()}")
        donnees_prod["eolien"][annee]    = pd.to_numeric(df["Eolien"],      errors="coerce").reset_index(drop=True)
        donnees_prod["pv"][annee]        = pd.to_numeric(df["Solaire"],     errors="coerce").reset_index(drop=True)
        donnees_prod["hydro"][annee]     = pd.to_numeric(df["Hydraulique"], errors="coerce").reset_index(drop=True)
        donnees_prod["timestamp"][annee] = df["timestamp"].reset_index(drop=True)
    return donnees_prod

# ── Chargement des données ────────────────────────────────────────────────────
df_meteo = pd.read_csv("data/meteo_openmeteo_2021_2023.csv")
df_meteo["timestamp"] = pd.to_datetime(df_meteo["timestamp"])
df_meteo = df_meteo[df_meteo["timestamp"].dt.minute.isin([0, 30])].reset_index(drop=True)
print(f"Météo : {len(df_meteo)} mesures | {df_meteo['timestamp'].min()} → {df_meteo['timestamp'].max()}")

production = donnees_prod()
dfs = []
for annee in [2021, 2022, 2023]:
    df_prod = pd.DataFrame({
        'timestamp': production['timestamp'][annee].values,
        'pv':        production['pv'][annee].values,
    })
    dfs.append(df_prod)
df_prod_all = pd.concat(dfs, ignore_index=True)

# ── Fusion ────────────────────────────────────────────────────────────────────
df_merge = pd.merge(df_meteo, df_prod_all, on="timestamp", how="inner")
print(f"Après fusion : {len(df_merge)} lignes")

# ── Agrégation par jour ───────────────────────────────────────────────────────
df_merge["date"] = df_merge["timestamp"].dt.date
df_jour = df_merge.groupby("date").agg(
    pv_journalier   = ("pv",               "sum"),
    temperature_moy = ("temperature",      "mean"),
    rayonnement_moy = ("rayonnement_reel", "mean"),
    rayonnement_std = ("rayonnement_reel", "std"),
    rayonnement_max = ("rayonnement_reel", "max"),
    rayonnement_min = ("rayonnement_reel", "min"),
).reset_index()

df_jour["rayonnement_std"] = df_jour["rayonnement_std"].fillna(0)
df_jour["date"] = pd.to_datetime(df_jour["date"])

# ── Heure du pic de rayonnement ───────────────────────────────────────────────
heure_pic = df_merge.loc[
    df_merge.groupby("date")["rayonnement_reel"].idxmax(), ["date", "timestamp"]
]
heure_pic["heure_pic"] = heure_pic["timestamp"].dt.hour + heure_pic["timestamp"].dt.minute / 60
heure_pic = heure_pic[["date", "heure_pic"]]
heure_pic["date"] = pd.to_datetime(heure_pic["date"])
df_jour = pd.merge(df_jour, heure_pic, on="date", how="left")

# ── Variables explicatives ────────────────────────────────────────────────────
df_jour["jour_annee"]    = df_jour["date"].dt.dayofyear
df_jour["sin_jour"]      = np.sin(2 * np.pi * df_jour["jour_annee"] / 365)
df_jour["cos_jour"]      = np.cos(2 * np.pi * df_jour["jour_annee"] / 365)
df_jour["sin_heure_pic"] = np.sin(2 * np.pi * df_jour["heure_pic"] / 24)
df_jour["cos_heure_pic"] = np.cos(2 * np.pi * df_jour["heure_pic"] / 24)

X = df_jour[["rayonnement_moy", "temperature_moy", "sin_jour", "cos_jour",
             "rayonnement_std", "sin_heure_pic", "cos_heure_pic"]]
y = df_jour["pv_journalier"]

# ── Modèles ───────────────────────────────────────────────────────────────────
train_size = int(0.75 * len(df_jour))
X_train, y_train = X[:train_size], y[:train_size]
X_test,  y_test  = X[train_size:], y[train_size:]

modeles = {
    "Régression linéaire": LinearRegression(),
    "Random Forest":       RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
}

resultats = {}
for nom, model in modeles.items():
    model.fit(X_train, y_train)
    y_pred_train = model.predict(X_train)
    y_pred_test  = model.predict(X_test)

    r2_train = r2_score(y_train, y_pred_train)
    r2_test  = r2_score(y_test,  y_pred_test)
    rmse     = np.sqrt(mean_squared_error(y_test, y_pred_test))
    mae      = mean_absolute_error(y_test, y_pred_test)

    # Cross-validation
    kf     = KFold(n_splits=5, shuffle=False)
    scores = cross_val_score(model, X, y, cv=kf, scoring="r2")

    resultats[nom] = {
        "r2_train": r2_train,
        "r2_test":  r2_test,
        "rmse":     rmse,
        "mae":      mae,
        "cv_mean":  scores.mean(),
        "cv_std":   scores.std(),
        "y_pred":   y_pred_test
    }

    # Overfitting / underfitting
    if r2_train - r2_test > 0.1:
        statut = "⚠ Overfitting détecté"
    elif r2_test < 0.4:
        statut = "⚠ Underfitting détecté"
    else:
        statut = "✓ Bon équilibre train/test"

    print(f"\n{'='*45}")
    print(f"Modèle : {nom}")
    print(f"{'='*45}")
    print(f"  R² train          : {r2_train:.4f}")
    print(f"  R² test           : {r2_test:.4f}  {statut}")
    print(f"  RMSE              : {rmse:.2f} MWh")
    print(f"  MAE               : {mae:.2f} MWh")
    print(f"  CV R² moyen       : {scores.mean():.4f}")
    print(f"  CV écart-type     : {scores.std():.4f}")
    print(f"  CV R² par pli     : {[round(s,3) for s in scores]}")

# ── Graphique 1 — Prédictions vs Réalité ─────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for ax, (nom, res) in zip(axes, resultats.items()):
    sns.scatterplot(x=y_test, y=res["y_pred"], alpha=0.4, s=15, ax=ax)
    ax.plot([y_test.min(), y_test.max()],
            [y_test.min(), y_test.max()], 'r--', linewidth=2, label="Prédiction parfaite")
    ax.set_xlabel("Production réelle (MWh)")
    ax.set_ylabel("Production prédite (MWh)")
    ax.set_title(f"{nom} — R² = {res['r2_test']:.2f}")
    ax.legend()

plt.suptitle("Prédictions vs Réalité", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("graph1_predictions.png", dpi=150)
print("\nGraphique 1 sauvegardé")

# ── Graphique 2 — Série temporelle ───────────────────────────────────────────
dates_test = df_jour["date"].iloc[train_size:].values

plt.figure(figsize=(12, 5))
sns.lineplot(x=dates_test, y=y_test.values,
             label="Réelle", linewidth=1.5)
sns.lineplot(x=dates_test, y=resultats["Régression linéaire"]["y_pred"],
             label="Prédite (Régression)", linewidth=1.5, linestyle="--")
plt.xlabel("Date")
plt.ylabel("Production PV journalière (MWh)")
plt.title("Production PV réelle vs prédite — 2023")
plt.legend()
plt.tight_layout()
plt.savefig("graph2_serie_temporelle.png", dpi=150)
print("Graphique 2 sauvegardé")

plt.show()
print(f"\nNombre de jours : {len(df_jour)}")