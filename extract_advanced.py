from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import random
import subprocess
import os
from bs4 import BeautifulSoup
import tempfile

# Dictionnaire des ligues avec les noms des pays et leurs URL
ligues = {
    'France': '13/Statistiques-Ligue-1',
    'Italie': '11/Statistiques-Serie-A',
    'Espagne': '12/Statistiques-La-Liga',
    'Allemagne': '20/Statistiques-Bundesliga',
    'Angleterre': '9/Statistiques-Premier-League'
}
chrome_options = Options()
chrome_options.add_argument('--headless')  # Exécution sans interface graphique
chrome_options.add_argument('--disable-gpu')  # Désactive le GPU
chrome_options.add_argument("--no-sandbox")  # Important pour éviter certains problèmes dans CI
chrome_options.add_argument("--remote-debugging-port=9222")  # Pour des tests à distance si nécessaire

temp_dir = tempfile.mkdtemp()
chrome_options.add_argument(f"--user-data-dir={temp_dir}")
# Configuration Selenium avec le gestionnaire de ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service,options=chrome_options)


# Initialisation du service avec le gestionnaire de ChromeDriver
service = Service(ChromeDriverManager().install())

# Configuration du driver Selenium
driver = webdriver.Chrome(service=service,options=chrome_options)

# Fonction pour récupérer les statistiques d'une ligue en fonction d'un ID de tableau
def fetch_league_data(ligues, table_id, prefix):
    df_ligues = {}

    for pays, url_part in ligues.items():
        url = f'https://fbref.com/fr/comps/{url_part}'

        # Charger la page avec Selenium pour contourner Cloudflare
        driver.get(url)
        
        # Attendre que la page soit bien chargée
        time.sleep(random.uniform(3, 7))  # Pause pour attendre que la page charge

        # Récupérer le contenu de la page après chargement
        page_content = driver.page_source

        # Utiliser BeautifulSoup pour analyser le contenu
        soup = BeautifulSoup(page_content, 'html.parser')

        # Chercher le tableau spécifique dans la page
        table = soup.find("table", {"id": table_id})
        if not table:
            print(f"⚠️ Table {table_id} non trouvée pour {pays}.")
            continue

        tbody = table.find("tbody")
        if not tbody:
            print(f"⚠️ Aucun <tbody> trouvé pour {pays}.")
            continue

        teams = []
        stats = []

        # Analyser les lignes du tableau
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

        # Attendre un délai aléatoire pour éviter les blocages
        time.sleep(random.uniform(1, 3))

    return df_ligues

# Récupérer deux types de statistiques
df_ligues_stats = fetch_league_data(ligues, "stats_squads_standard_for", "stats_")
time.sleep(10)
df_ligues_advanced = fetch_league_data(ligues, "stats_squads_keeper_for", "full_")
time.sleep(10)
df_ligues_advanced2 = fetch_league_data(ligues, "stats_squads_standard_against", "adv")

# Sauvegarder les fichiers CSV
for pays in df_ligues_advanced.keys():
    df_merged = pd.merge(df_ligues_stats[pays], df_ligues_advanced[pays], left_index=True, right_index=True, how="outer")
    filename = f"Merged_{pays}.csv"
    df_merged.to_csv(filename, encoding='utf-8-sig')
    print(f"📁 Fichier {pays} sauvegardé : {filename}")
    
    # Commit et push vers GitHub
    GH_TOKEN = os.getenv("GH_TOKEN")
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

# Sauvegarder les données "Against"
for pays in df_ligues_advanced2.keys():
    filename = f"Against_{pays}.csv"
    df_ligues_advanced2[pays].to_csv(filename, encoding='utf-8-sig')
    print(f"📁 Fichier Against sauvegardé : {filename}")
    
    # Commit et push vers GitHub
    GH_TOKEN = os.getenv("GH_TOKEN")
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

# Fermer le navigateur une fois que tout est terminé
driver.quit()
