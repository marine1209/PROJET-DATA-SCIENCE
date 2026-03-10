# Ajouter les fonction de data cleaning dans cette feuille 

#Bibliothèques 
import pandas as pd 
import numpy as np 

# Ana : Production ENR et/ou Nucléaire 
def harmonize_data_DayAhead_price(chemin_fichier):
    # Lecture du fichier et création d'une copie pour ne pas toucher aux données originales
    df = pd.read_csv(chemin_fichier).copy()
    
    # On garde seulement les colonnes utiles et on renomme
    df = df[["MTU (UTC)", "Day-ahead Price (EUR/MWh)"]].copy()
    df = df.rename(columns={
        "MTU (UTC)": "MTU (CET/CEST)",
        "Day-ahead Price (EUR/MWh)": "Day-ahead Price [EUR/MWh]"
    })
    
    # On sépare la plage horaire en deux colonnes
    df[["Date_start", "Date_end"]] = df["MTU (CET/CEST)"].str.split(" - ", expand=True)
    df = df.drop(columns=["MTU (CET/CEST)"])
    
    # Conversion en datetime
    df["Date_start"] = pd.to_datetime(df["Date_start"], format="%d/%m/%Y %H:%M:%S", utc=True).dt.tz_localize(None)
    df["Date_end"] = pd.to_datetime(df["Date_end"], format="%d/%m/%Y %H:%M:%S", utc=True).dt.tz_localize(None)
    
    print(df.shape)
    print(df.head())
    return df
    

# Marie : Prix de l'énergie sur le marché SPOT
def clean_data_price (chemin_fichier):
    df = pd.read_csv(chemin_fichier)
    if df["BZN|FR"].isna().all(): # on vérifie que la colonne est vide avant de la supprimer
        df = df.drop(columns=["BZN|FR"])
        print('La colonne "BZN|FR" était vide et a été supprimée.')
    else:
        print('La colonne "BZN|FR" contient des données.')
    df=df.drop(columns=["Currency"])
    df[["Date_start", "Date_end"]] = df["MTU (CET/CEST)"].str.split(" - ", expand=True) 
    df = df.drop(columns=["MTU (CET/CEST)"]) # on supprime l'ancienne colonne de la plage horaire
    df["Date_start"] = pd.to_datetime(df["Date_start"], format="%d.%m.%Y %H:%M", utc = True).dt.tz_localize(None) # on change de le format de la date de début et de fin
    df["Date_end"] = pd.to_datetime(df["Date_end"], format="%d.%m.%Y %H:%M", utc = True).dt.tz_localize(None) # on change de le format de la date de fin
    print(df.shape)
    print(df.head())
    return df
#clean_data_price(".\Data\Day-ahead Prices_2019-2020.csv")
# Marine : Température & pseudo rayonnement

def clean_data_temperature (chemin_fichier): 
    fichier = pd.read_csv(chemin_fichier, sep=";")
    fichier["Horodate"] = pd.to_datetime(fichier["Horodate"], utc = True)
    fichier = fichier.drop(columns=["Année-Mois-Jour"])
    fichier = fichier.drop(columns = ["Année"])
    fichier = fichier.drop(columns = ["Mois"])
    fichier = fichier.drop(columns = ["Jour"])
    print(fichier.isna().sum())
    print(fichier.isnull().sum() )
    print(fichier.duplicated().sum())
    print(fichier.info())
    print(fichier.head())
    print(fichier.describe()) 
    return fichier
    
    
#def traitement_data_temperature(fichier_nettoye): 
    






