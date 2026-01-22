import os
import sys
import csv
import django

# ----------------------------
# Configuration Django
# ----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)  # <-- ajoute le projet au PYTHONPATH

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User

# ----------------------------
# Chemin vers le CSV des utilisateurs
# ----------------------------
USERS_CSV = os.path.join(BASE_DIR, 'import', 'users.csv')

# ----------------------------
# Fonction d'import utilisateurs
# ----------------------------
def import_users():
    if not os.path.exists(USERS_CSV):
        print("Fichier CSV utilisateurs introuvable :", USERS_CSV)
        return

    csv_usernames = set()
    with open(USERS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row['username'].strip()
            email = row['email'].strip()
            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', '').strip()
            if not username or username == 'Alex':  # Conserver le superuser Alex
                continue
            csv_usernames.add(username)

            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email, 'first_name': first_name, 'last_name': last_name}
            )
            if created:
                user.set_unusable_password()  # Mot de passe inutilisable, force le choix à la première connexion
                user.save()
                print(f"Utilisateur créé : {username}")
            else:
                # Mettre à jour l'email, first_name, last_name si changé
                updated = False
                if user.email != email:
                    user.email = email
                    updated = True
                if user.first_name != first_name:
                    user.first_name = first_name
                    updated = True
                if user.last_name != last_name:
                    user.last_name = last_name
                    updated = True
                if updated:
                    user.save()
                    print(f"Utilisateur mis à jour : {username}")

    # Supprimer les utilisateurs qui ne sont plus dans le CSV (sauf Alex)
    existing_users = User.objects.exclude(username='Alex')
    for user in existing_users:
        if user.username not in csv_usernames:
            print(f"Utilisateur supprimé : {user.username}")
            user.delete()

if __name__ == "__main__":
    import_users()