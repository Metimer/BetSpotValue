import requests
from bs4 import BeautifulSoup
import pandas as pd
import subprocess

# Dictionnaire des ligues avec les noms des pays et leurs URL
ligues = {
    'France': '13/Statistiques-Ligue-1',
    'Italie': '11/Statistiques-Serie-A',
    'Espagne': '12/Statistiques-La-Liga',
    'Allemagne': '20/Statistiques-Bundesliga',
    'Angleterre': '9/Statistiques-Premier-League'
}

navigator = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)'

df_ligues = {}

# Boucle à travers les ligues
for pays, url_part in ligues.items():
    url = f'https://fbref.com/fr/comps/{url_part}'
    response = requests.get(url, headers={'User-Agent': navigator})

    if response.status_code != 200:
        print(f"❌ Erreur lors de la récupération de la page pour {pays}.")
        continue

    soup = BeautifulSoup(response.text, 'html.parser')

    # Récupérer uniquement la section <tbody>
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

    # Configuration GitHub (remplace "ton-utilisateur" et "ton-repo" par les tiens)
    repo_url = "https://github.com/Metimer/BetValueSpot.git"

    # Commandes Git
    commands = [
    "git add " + csv_filename,
    'git commit -m "Mise à jour automatique des classements"',
    "git push origin main"
]

    # Exécuter les commandes Git
    for command in commands:
      subprocess.run(command, shell=True)

      print("CSV mis à jour et envoyé sur GitHub avec succès.")
