import os
import sys
import csv
import time
import django
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from django.utils import timezone

# ----------------------------
# Configuration Django
# ----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)  # <-- ajoute le projet au PYTHONPATH

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from pronostics.models import Match, Equipe, Saison
from watchers.import_users import import_users

# ----------------------------
# Chemin vers le CSV à surveiller
# ----------------------------
CSV_FILE = os.path.join(BASE_DIR, 'import', 'matchs.csv')

# ----------------------------
# Chemin vers le CSV des utilisateurs
# ----------------------------
USERS_CSV = os.path.join(BASE_DIR, 'import', 'users.csv')

# ----------------------------
# Fonction d'import CSV
# ----------------------------
def import_csv():
    if not os.path.exists(CSV_FILE):
        print("Fichier CSV introuvable :", CSV_FILE)
        return

    csv_matches = []
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) < 8:
                continue
            saison_annee = row[0]
            journee = int(row[1]) if row[1] else 1
            equipe_domicile_nom = row[2]
            equipe_exterieure_nom = row[3]
            date_str = row[4]
            time_str = row[5]
            score_domicile = row[6] if len(row) > 6 and row[6] else None
            score_exterieure = row[7] if len(row) > 7 and row[7] else None

            # Créer les équipes si elles n'existent pas
            equipe_domicile, _ = Equipe.objects.get_or_create(nom=equipe_domicile_nom)
            equipe_exterieure, _ = Equipe.objects.get_or_create(nom=equipe_exterieure_nom)

            # Créer la saison si elle n'existe pas
            saison, _ = Saison.objects.get_or_create(annee=saison_annee)

            # Conversion en datetime
            match_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            match_datetime = timezone.make_aware(match_datetime)

            # Conversion scores en int si présent
            score_domicile = int(score_domicile) if score_domicile else None
            score_exterieure = int(score_exterieure) if score_exterieure else None

            csv_matches.append({
                'saison': saison,
                'journee': journee,
                'equipe_domicile': equipe_domicile,
                'equipe_exterieure': equipe_exterieure,
                'date': match_datetime,
                'score_domicile': score_domicile,
                'score_exterieur': score_exterieure
            })

    # Collecter les clés des matchs du CSV
    csv_keys = {(m['equipe_domicile'], m['equipe_exterieure'], m['date']) for m in csv_matches}

    # Création ou mise à jour des matchs du CSV
    for match_data in csv_matches:
        match, created = Match.objects.update_or_create(
            equipe_domicile=match_data['equipe_domicile'],
            equipe_exterieure=match_data['equipe_exterieure'],
            date=match_data['date'],
            defaults={
                'saison': match_data['saison'],
                'journee': match_data['journee'],
                'score_domicile': match_data['score_domicile'],
                'score_exterieur': match_data['score_exterieur']
            }
        )
        if created:
            print(f"Match créé : {match} à {match.date}")
        else:
            print(f"Match mis à jour : {match} à {match.date}, scores {match.score_domicile}-{match.score_exterieur}")

    # Supprimer les matchs qui ne sont plus dans le CSV
    existing_matches = Match.objects.all()
    for match in existing_matches:
        key = (match.equipe_domicile, match.equipe_exterieure, match.date)
        if key not in csv_keys:
            print(f"Match supprimé : {match} à {match.date}")
            match.delete()

# ----------------------------
# Watchdog Event Handler
# ----------------------------
class CSVHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('matchs.csv'):
            print("CSV matchs modifié, import en cours...")
            import_csv()
        elif event.src_path.endswith('users.csv'):
            print("CSV users modifié, import en cours...")
            import_users()

# ----------------------------
# Boucle principale
# ----------------------------
if __name__ == "__main__":
    print("Surveillance des CSV en cours :", os.path.dirname(CSV_FILE))
    event_handler = CSVHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(CSV_FILE), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
