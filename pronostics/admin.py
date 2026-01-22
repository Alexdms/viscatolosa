from django.contrib import admin
from .models import Match, Pronostic, Saison, Equipe

class EquipeInline(admin.TabularInline):
    model = Saison.equipes.through
    extra = 0

@admin.register(Saison)
class SaisonAdmin(admin.ModelAdmin):
    list_display = ('annee',)
    inlines = [EquipeInline]

@admin.register(Equipe)
class EquipeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'logo')

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('journee', 'saison', 'equipe_domicile', 'equipe_exterieure', 'date', 'score_domicile', 'score_exterieur')
    ordering = ('date',)

@admin.register(Pronostic)
class PronosticAdmin(admin.ModelAdmin):
    list_display = ('user', 'match', 'score_domicile', 'score_exterieur', 'points')
