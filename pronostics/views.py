from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Match, Pronostic
from .forms import PronosticForm, UserUpdateForm

# -----------------------
# Gestion des utilisateurs
# -----------------------

def login_user(request):
    error = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST.get('password')
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            error = "Utilisateur inconnu."
        else:
            if password:  # Connexion normale
                user_auth = authenticate(request, username=username, password=password)
                if user_auth:
                    login(request, user_auth)
                    return redirect('pronostics:accueil')
                else:
                    error = "Mot de passe incorrect."
            elif email and not new_password:  # Vérification pour première connexion
                if not user.has_usable_password():
                    if user.email == email:
                        request.session['verified_user_id'] = user.id
                        return redirect('pronostics:set_password')
                    else:
                        error = "Adresse email incorrecte."
                else:
                    error = "Vous avez déjà un mot de passe. Utilisez la connexion normale."
            elif new_password:  # Définition du mot de passe (depuis set_password)
                pass  # Géré dans set_password
            else:
                error = "Veuillez fournir un mot de passe ou une adresse email."
    
    return render(request, 'pronostics/login.html', {'error': error})

def set_password(request):
    user_id = request.session.get('verified_user_id')
    if not user_id:
        return redirect('pronostics:login')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        del request.session['verified_user_id']
        return redirect('pronostics:login')
    
    if request.method == 'POST':
        form = SetPasswordForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            login(request, user)  # Connecter l'utilisateur après définition du mot de passe
            del request.session['verified_user_id']
            return redirect('pronostics:accueil')
        else:
            print("Form errors:", form.errors)
    else:
        form = SetPasswordForm(user=user)
    
    return render(request, 'pronostics/set_password.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('pronostics:login')


# -----------------------
# Pages principales
# -----------------------

@login_required
def accueil(request):
    # Affiche le prochain match à pronostiquer
    prochain_match = Match.objects.filter(date__gte=timezone.now()).order_by('date').first()
    return render(request, 'pronostics/accueil.html', {'prochain_match': prochain_match})


@login_required
def mes_pronos(request):
    # Récupère les pronostics de l'utilisateur
    pronos = Pronostic.objects.select_related('match').filter(user=request.user).order_by('match__date')

    # Calcul à la volée des points
    for p in pronos:
        p.points = p.calculer_points()

    return render(request, 'pronostics/mes_pronos.html', {'pronos': pronos, 'now': timezone.now()})


@login_required
def classement(request):
    # Calcul des points de tous les utilisateurs à la volée
    all_pronos = Pronostic.objects.select_related('match', 'user').all()
    scores = {}
    for p in all_pronos:
        pts = p.calculer_points()
        scores[p.user.username] = scores.get(p.user.username, 0) + pts

    # Prochain match
    prochain_match = Match.objects.filter(date__gte=timezone.now()).order_by('date').first()

    # Pour chaque user, prono sur le prochain match
    users = User.objects.all()
    for user in users:
        username = user.username
        if username not in scores:
            scores[username] = 0
        # Trouver prono sur prochain match
        prono_semaine = "SP"
        points_semaine = 0
        if prochain_match:
            try:
                prono = Pronostic.objects.get(user=user, match=prochain_match)
                prono_semaine = f"{prono.score_domicile}-{prono.score_exterieur}"
                points_semaine = prono.calculer_points()
            except Pronostic.DoesNotExist:
                pass
        # Ajouter au scores
        scores[username] = {
            'total': scores[username],
            'prono_semaine': prono_semaine,
            'points_semaine': points_semaine
        }

    # Transformer en liste triée pour le template
    classement_list = [{'username': u, 'total': d['total'], 'prono_semaine': d['prono_semaine'], 'points_semaine': d['points_semaine']} for u, d in scores.items()]
    classement_list.sort(key=lambda x: x['total'], reverse=True)

    return render(request, 'pronostics/classement.html', {'classement': classement_list, 'prochain_match': prochain_match})


@login_required
def mon_compte(request):
    if request.method == 'POST':
        # Formulaire mise à jour email/username
        u_form = UserUpdateForm(request.POST, instance=request.user)
        # Formulaire changement de mot de passe
        p_form = PasswordChangeForm(user=request.user, data=request.POST)

        if 'update_user' in request.POST and u_form.is_valid():
            u_form.save()
            return redirect('pronostics:mon_compte')

        if 'change_password' in request.POST and p_form.is_valid():
            user = p_form.save()
            update_session_auth_hash(request, user)  # Rester connecté après changement
            return redirect('pronostics:mon_compte')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = PasswordChangeForm(user=request.user)

    return render(request, 'pronostics/mon_compte.html', {'u_form': u_form, 'p_form': p_form})


@login_required
def pronostiquer(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    if not match.can_pronostiquer():
        return redirect('pronostics:accueil')

    pronostic, created = Pronostic.objects.get_or_create(user=request.user, match=match)
    if request.method == 'POST':
        form = PronosticForm(request.POST, instance=pronostic)
        if form.is_valid():
            form.save()
            return redirect('pronostics:mes_pronos')
    else:
        form = PronosticForm(instance=pronostic)

    return render(request, 'pronostics/pronostiquer.html', {
        'form': form,
        'match': match,
        'pronostic': pronostic
    })
