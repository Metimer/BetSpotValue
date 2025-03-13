from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import subprocess
import os
import time

# Dictionnaire des ligues avec les noms des pays et leurs URL
ligues = {
    'France': '13/Statistiques-Ligue-1',
    'Italie': '11/Statistiques-Serie-A',
    'Espagne': '12/Statistiques-La-Liga',
    'Allemagne': '20/Statistiques-Bundesliga',
    'Angleterre': '9/Statistiques-Premier-League'
}
chrome_options = Options()
chrome_options.add_argument("--user-data-dir=/tmp/chrome_data")
# Configuration Selenium avec le gestionnaire de ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service,options=chrome_options)

# Initialisation du dictionnaire des ligues
df_ligues = {}

# Boucle à travers les ligues
for pays, url_part in ligues.items():
    url = f'https://fbref.com/fr/comps/{url_part}'
    
    # Charger la page avec Selenium
    driver.get(url)

    # Attendre que la page soit complètement chargée
    time.sleep(5)  # Temps d'attente arbitraire de 5 secondes, à ajuster si nécessaire

    # Récupérer le contenu de la page après chargement
    page_source = driver.page_source

    # Utiliser BeautifulSoup pour analyser le contenu HTML
    soup = BeautifulSoup(page_source, 'html.parser')

    # Récupérer uniquement la section <tbody> du tableau
    tbody = soup.find("tbody")
    if not tbody:
        print(f"⚠️ Aucun tableau trouvé pour {pays}.")
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
                row_data[data_stat] = text

        if current_team:
            stats.append(row_data)

    # Convertir en DataFrame pandas
    df = pd.DataFrame(stats, index=teams).fillna('N/A')

    # Stocker le DataFrame dans un dictionnaire
    df_ligues[pays] = df

    print(f"✅ Données récupérées pour {pays} ({url_part})")

# Sauvegarder les résultats dans des fichiers CSV
for pays, df in df_ligues.items():
    # Enregistrer le CSV dans le répertoire du projet (à la racine)
    csv_filename = f"Classement_{ligues[pays].split('/')[-1]}.csv"
    df.to_csv(csv_filename)

    # Utilisation du token GitHub pour pousser les fichiers CSV
    GH_TOKEN = os.getenv("GH_TOKEN")  # Récupère le token depuis GitHub Actions
    repo_url = f"https://x-access-token:{GH_TOKEN}@github.com/Metimer/BetSpotValue.git"

    # Commandes Git pour ajouter, committer et pousser les changements
    commands = [
        "git add .",  # Ajout des fichiers modifiés
        'git commit -m "Mise à jour automatique des statistiques"',  # Commit des modifications
        f"git pull --rebase {repo_url} main",  # Récupérer les derniers changements avec rebase
        f"git push {repo_url} HEAD:main"  # Pousser les changements vers le dépôt GitHub
    ]

    # Exécuter les commandes Git
    for command in commands:
        subprocess.run(command, shell=True)

    print(f"✅ CSV mis à jour et envoyé sur GitHub pour {pays}.")

# Fermer le navigateur une fois que tout est terminé
driver.quit()
