from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# -------------------------------
# Modèle Equipe
# -------------------------------
class Equipe(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)

    def __str__(self):
        return self.nom

# -------------------------------
# Modèle Saison
# -------------------------------
class Saison(models.Model):
    annee = models.CharField(max_length=10, unique=True)  # ex: "2025-2026"
    equipes = models.ManyToManyField(Equipe, related_name='saisons')

    def __str__(self):
        return self.annee

# -------------------------------
# Modèle Match
# -------------------------------
class Match(models.Model):
    saison = models.ForeignKey(Saison, on_delete=models.CASCADE, default=1)
    journee = models.IntegerField(default=1)
    equipe_domicile = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='matchs_domicile')
    equipe_exterieure = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='matchs_exterieure')
    score_domicile = models.IntegerField(null=True, blank=True)
    score_exterieur = models.IntegerField(null=True, blank=True)
    date = models.DateTimeField()

    def is_played(self):
        """Retourne True si le match a un score renseigné"""
        return self.score_domicile is not None and self.score_exterieur is not None

    def can_pronostiquer(self):
        """Retourne True si le match peut encore être pronostiqué"""
        return timezone.now() < self.date

    def __str__(self):
        return f"{self.equipe_domicile.nom} - {self.equipe_exterieure.nom}"

# -------------------------------
# Modèle Pronostic
# -------------------------------
class Pronostic(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    score_domicile = models.IntegerField(null=True, blank=True)
    score_exterieur = models.IntegerField(null=True, blank=True)
    points = models.IntegerField(default=0)

    def calculer_points(self):
        """
        Calcule les points du pronostic en fonction du score réel du match.
        Retourne 0 si le match n'a pas encore été joué ou si le pronostic est incomplet.
        """
        if not self.match.is_played() or self.score_domicile is None or self.score_exterieur is None:
            return 0

        # Pronostic exact
        if self.score_domicile == self.match.score_domicile and self.score_exterieur == self.match.score_exterieur:
            return 5

        # Match nul
        if self.match.score_domicile == self.match.score_exterieur:
            if self.score_domicile == self.score_exterieur:
                return 4  # Nul correct mais pas exact
            return 0

        # Bonne différence de buts
        if (self.score_domicile - self.score_exterieur) == (self.match.score_domicile - self.match.score_exterieur):
            return 4

        # Vainqueur trouvé sans le bon écart
        if (self.score_domicile > self.score_exterieur and self.match.score_domicile > self.match.score_exterieur) or \
           (self.score_domicile < self.score_exterieur and self.match.score_domicile < self.match.score_exterieur):
            return 3

        # Tout faux
        return 0

    def save(self, *args, **kwargs):
        """Met à jour les points automatiquement avant de sauvegarder"""
        self.points = self.calculer_points()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.match}"
