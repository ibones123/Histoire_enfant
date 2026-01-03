from django.urls import path
from . import views

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("inscription/", views.inscription, name="inscription"),
    path("connexion/", views.connexion, name="connexion"),
    path("deconnexion/", views.deconnexion, name="deconnexion"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("enfant/ajouter/", views.ajouter_enfant, name="ajouter_enfant"),
    path("histoire/creer/", views.creer_histoire, name="creer_histoire"),
    path("histoire/<int:histoire_id>/", views.voir_histoire, name="voir_histoire"),
    path("histoire/<int:histoire_id>/audio/", views.audio_histoire, name="audio_histoire"),
    path("chapitre/<int:chapitre_id>/audio/", views.audio_chapitre, name="audio_chapitre"),
    path("generation/<int:histoire_id>/", views.generation_histoire, name="generation_histoire"),
    path("api/histoire/<int:histoire_id>/generer_image/", views.api_generer_image, name="api_generer_image"),

]
