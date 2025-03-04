import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os 
import subprocess


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

# Fonction pour sauvegarder les DataFrames fusionnés et pousser les changements sur GitHub
def save_merged_data(df_ligues_stats, df_ligues_advanced, output_dir, repo_url):
    for pays in df_ligues_stats.keys():
        if pays in df_ligues_advanced:
            # Fusion sur l'index (nom de l'équipe)
            df_merged = pd.merge(df_ligues_stats[pays], df_ligues_advanced[pays], left_index=True, right_index=True, how="outer", suffixes=('_stats', '_advanced'))

            # Nom du fichier basé sur la ligue
            filename = f"Merged_{ligues[pays].split('/')[-1]}.csv"
            filepath = os.path.join(output_dir, filename)

            # Sauvegarde du fichier CSV fusionné
            df_merged.to_csv(filepath, encoding='utf-8-sig')
            print(f"📁 Fichier fusionné sauvegardé : {filepath}")

            # Pousser le fichier sur GitHub
            git_push(filepath, repo_url)

# Fonction pour effectuer le push des changements sur GitHub
def git_push(csv_filename, repo_url):
    # Ajouter, commettre et pousser les fichiers modifiés
    try:
        subprocess.run(f"git add {csv_filename}", shell=True, check=True)
        commit_message = f"📈 Mise à jour automatique de {csv_filename}"
        subprocess.run(f'git commit -m "{commit_message}"', shell=True, check=True)
        subprocess.run("git push origin main", shell=True, check=True)
        print(f"✔️ {csv_filename} mis à jour sur GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution des commandes Git : {e}")

# 🔹 Récupérer deux types de statistiques (exemple : Standard et Avancées)
df_ligues_stats = fetch_league_data(ligues, "stats_squads_standard_for", "stats_")
time.sleep(60)
df_ligues_advanced = fetch_league_data(ligues, "stats_squads_keeper_for", "full_")  # Exemple d'un autre tableau
time.sleep(60)
df_ligues_advanced2 = fetch_league_data(ligues, "stats_squads_standard_against", "adv")  # Exemple d'un autre tableau


# 🔹 Fusionner les DataFrames correspondants et les exporter
output_directory = 'C:\\Users\\metin\\OneDrive\\Bureau\\Projet3\\p3'
repo_url = "https://github.com/Metimer/BetSpotValue.git"  # Remplace par ton URL de repo GitHub

save_merged_data(df_ligues_stats, df_ligues_advanced, output_directory, repo_url)

# Sauvegarder les données "Against" séparément et pousser
for pays in df_ligues_advanced2.keys():
    filename = f"Against_{pays}.csv"
    filepath = os.path.join(output_directory, filename)
    df_ligues_advanced2[pays].to_csv(filepath, encoding='utf-8-sig')
    
    # Pousser chaque fichier "Against" sur GitHub
    git_push(filepath, repo_url)
