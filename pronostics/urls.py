from django.urls import path
from . import views

app_name = 'pronostics'

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('mes-pronos/', views.mes_pronos, name='mes_pronos'),
    path('classement/', views.classement, name='classement'),
    path('mon-compte/', views.mon_compte, name='mon_compte'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('set-password/', views.set_password, name='set_password'),
    path('pronostiquer/<int:match_id>/', views.pronostiquer, name='pronostiquer'),
]
