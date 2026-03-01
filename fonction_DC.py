# Ajouter les fonction de data cleaning dans cette feuille 

#Bibliothèques 
import pandas as pd 
import numpy as np 

# Ana : Production ENR et/ou Nucléaire 

# Marie : Prix de l'énergie sur le marché SPOT

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
    






