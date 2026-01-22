from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Pronostic

# Formulaire de pronostic
class PronosticForm(forms.ModelForm):
    class Meta:
        model = Pronostic
        fields = ['score_domicile', 'score_exterieur']
        widgets = {
            'score_domicile': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Score domicile'}),
            'score_exterieur': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Score extérieur'}),
        }

# Formulaire de mise à jour utilisateur (email seulement)
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

# Formulaire mise à jour email seul (optionnel si tu veux séparé)
class UpdateEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

# Formulaire changement de mot de passe
class UpdatePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Ancien mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label="Confirmation du nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
