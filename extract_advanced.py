import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import subprocess
import os 

# Dictionnaire des ligues avec les noms des pays et leurs URL
ligues = {
    'France': '13/Statistiques-Ligue-1',
    'Italie': '11/Statistiques-Serie-A',
    'Espagne': '12/Statistiques-La-Liga',
    'Allemagne': '20/Statistiques-Bundesliga',
    'Angleterre': '9/Statistiques-Premier-League'
}


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

# Fonction pour récupérer les statistiques d'une ligue en fonction d'un ID de tableau
def fetch_league_data(ligues, table_id, prefix):
    df_ligues = {}

    for pays, url_part in ligues.items():
        url = f'https://fbref.com/fr/comps/{url_part}'
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"❌ Erreur lors de la récupération de la page pour {pays}.")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table", {"id": table_id})  # On cherche un tableau spécifique
        if not table:
            print(f"⚠️ Table {table_id} non trouvée pour {pays}.")
            continue

        tbody = table.find("tbody")
        if not tbody:
            print(f"⚠️ Aucun <tbody> trouvé pour {pays}.")
            continue

        teams = []
        stats = []

        for row in tbody.find_all("tr"):
            cells = row.find_all(attrs={"data-stat": True})
            row_data = {}

            current_team = None
            for cell in cells:
                data_stat = cell["data-stat"]
                text = cell.get_text(strip=True)

                if data_stat == "team":
                    current_team = text
                    teams.append(current_team)
                elif current_team:
                    row_data[f"{prefix}{data_stat}"] = text  # On ajoute un préfixe aux colonnes

            if current_team:
                stats.append(row_data)

        # Convertir en DataFrame pandas et remplir les valeurs manquantes
        df = pd.DataFrame(stats, index=teams).fillna('N/A')

        df_ligues[pays] = df

        print(f"✅ Données récupérées pour {pays} ({table_id})")

    return df_ligues


# 🔹 Récupérer deux types de statistiques (exemple : Standard et Avancées)
df_ligues_stats = fetch_league_data(ligues, "stats_squads_standard_for", "stats_")
time.sleep(10)
df_ligues_advanced = fetch_league_data(ligues, "stats_squads_keeper_for", "full_")  # Exemple d'un autre tableau
time.sleep(10)
df_ligues_advanced2 = fetch_league_data(ligues, "stats_squads_standard_against", "adv")  # Exemple d'un autre tableau


# Sauvegarder les données "Against" séparément
for pays in df_ligues_advanced.keys():
    df_merged = pd.merge(df_ligues_stats[pays], df_ligues_advanced[pays], left_index=True, right_index=True, how="outer")
    filename = f"Against_{pays}.csv"   
    df_merged.to_csv(filename, encoding='utf-8-sig')
    print(f"📁 Fichier Against sauvegardé : {filename}")
    GH_TOKEN = os.getenv("GH_TOKEN")  # Récupère le token depuis GitHub Actions
    repo_url = f"https://x-access-token:{GH_TOKEN}@github.com/Metimer/BetSpotValue.git"

    commands = [
    "git add .",
    'git commit -m "Mise à jour automatique des stats avancées"',
    f"git pull --rebase {repo_url} main",  # Ajout du pull avec rebase
    f"git push {repo_url} HEAD:main"
    ]

    # Exécuter les commandes Git
    for command in commands:
        subprocess.run(command, shell=True)

    print(f"CSV pour {pays} mis à jour et envoyé sur GitHub avec succès.")

# Sauvegarder les données "Against" séparément
for pays in df_ligues_advanced2.keys():
    filename = f"Against_{pays}.csv"
    df_ligues_advanced2[pays].to_csv(filename, encoding='utf-8-sig')
    print(f"📁 Fichier Against sauvegardé : {filename}")
    GH_TOKEN = os.getenv("GH_TOKEN")  # Récupère le token depuis GitHub Actions
    repo_url = f"https://x-access-token:{GH_TOKEN}@github.com/Metimer/BetSpotValue.git"

    commands = [
    "git add .",
    'git commit -m "Mise à jour automatique des stats avancées"',
    f"git pull --rebase {repo_url} main",  # Ajout du pull avec rebase
    f"git push {repo_url} HEAD:main"
    ]

    # Exécuter les commandes Git
    for command in commands:
        subprocess.run(command, shell=True)

    print(f"CSV pour {pays} mis à jour et envoyé sur GitHub avec succès.")
