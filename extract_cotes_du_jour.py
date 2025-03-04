import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import subprocess

# Dictionnaire des ligues avec les noms des pays et les suffixes urls
ligues = {
    'France': 'l1-mcdonald-s/45452',
    'Italie': 'serie-a/45402',
    'Espagne': 'laliga/45456',
    'Allemagne': 'bundesliga-1/45399',
    'Angleterre': 'premier-league/45457'
}

navigator = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)'

# Initialisation des listes pour stocker les données
data = {
    'Pays': [],  
    'Ligue': [],  
    'Numéro de Pari': [],
    'Date du Match': [],
    'Heure de Fin de Validité': [],
    'Equipe Domicile': [],
    'Equipe Extérieure': [],
    'Cote Domicile': [],
    'Cote Nul': [],
    'Cote Extérieur': []
}

# Boucle à travers les ligues
for pays, url_part in ligues.items():
    url = f'https://www.pointdevente.parionssport.fdj.fr/paris-ouverts/football/{url_part}'
    response = requests.get(url, headers={'User-Agent': navigator})

    if response.status_code != 200:
        print(f"Erreur lors de la récupération de la page pour {pays}.")
        continue

    soup = BeautifulSoup(response.text, 'html.parser')

    # Récupération des numéros de paris, des dates et heures
    dates_heures = soup.find_all('p', class_='match-home_time')
    pattern = r"N°(\d+)\s+.*Fin de valid\.\s+(\d{2}\/\d{2})\s+(\d{2}h\d{2})"

    for date_heure in dates_heures:
        match_text = date_heure.text.strip()
        match_result = re.match(pattern, match_text)
        if match_result:
            data['Pays'].append(pays)  # Ajout du pays
            data['Ligue'].append(url_part.split('/')[0])  # Ajout du nom de la ligue à partir de l'URL
            data['Numéro de Pari'].append(match_result.group(1))
            data['Date du Match'].append(match_result.group(2))
            data['Heure de Fin de Validité'].append(match_result.group(3))

    # Récupération des matchs et équipes
    domicile, exterieur = [], []
    matchs = soup.find_all('div', class_='match-home_title')
    match_pattern = r"([^\-]+)-([^\-]+)"

    for match_ in matchs:
        match_text = match_.text.strip()
        match_result = re.match(match_pattern, match_text)
        if match_result:
            domicile.append(match_result.group(1).strip())
            exterieur.append(match_result.group(2).strip())

    # Extraction des cotes
    cotes_vdomicile, cotes_nul, cotes_vexterieur = [], [], []
    cotes_vdomicile_elements = soup.find_all('span', class_='outcomeButton_value', attrs={"data": "app-market-template|outcome-1|outcomeButton_value"})
    for cote in cotes_vdomicile_elements:
        cotes_vdomicile.append(cote.text.strip())

    cotes_nul_elements = soup.find_all('span', class_='outcomeButton_value', attrs={"data": "app-market-template|outcome-N|outcomeButton_value"})
    for cote in cotes_nul_elements:
        cotes_nul.append(cote.text.strip())

    cotes_vexterieur_elements = soup.find_all('span', class_='outcomeButton_value', attrs={"data": "app-market-template|outcome-2|outcomeButton_value"})
    for cote in cotes_vexterieur_elements:
        cotes_vexterieur.append(cote.text.strip())

    # Ajout des données dans le dictionnaire
    for i in range(len(domicile)):
        data['Equipe Domicile'].append(domicile[i])
        data['Equipe Extérieure'].append(exterieur[i])
        data['Cote Domicile'].append(cotes_vdomicile[i] if i < len(cotes_vdomicile) else None)
        data['Cote Nul'].append(cotes_nul[i] if i < len(cotes_nul) else None)
        data['Cote Extérieur'].append(cotes_vexterieur[i] if i < len(cotes_vexterieur) else None)

# Création du DataFrame à partir du dictionnaire
df = pd.DataFrame(data)

# Enregistrer le CSV dans le répertoire du projet (à la racine)
csv_filename = "cotes_du_jour.csv"
df.to_csv(csv_filename, index=False)

# Configuration GitHub (remplace "ton-utilisateur" et "ton-repo" par les tiens)
repo_url = "https://github.com/ton-utilisateur/ValueBetSpotter.git"

# Commandes Git
commands = [
    "git add " + csv_filename,
    'git commit -m "Mise à jour automatique des cotes"',
    "git push origin main"
]

# Exécuter les commandes Git
for command in commands:
    subprocess.run(command, shell=True)

print("CSV mis à jour et envoyé sur GitHub avec succès.")
