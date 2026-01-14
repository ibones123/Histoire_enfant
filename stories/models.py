from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Enfant(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE)
    prenom = models.CharField(max_length=100)
    age = models.IntegerField()

    def __str__(self):
        return self.prenom


class Histoire(models.Model):
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE)
    titre = models.CharField(max_length=200)
    date_creation = models.DateTimeField(auto_now_add=True)
    morale = models.TextField(blank=True)

    def __str__(self):
        return self.titre


class Chapitre(models.Model):
    histoire = models.ForeignKey(Histoire, on_delete=models.CASCADE)
    numero = models.IntegerField()
    titre = models.CharField(max_length=200)
    texte = models.TextField()
    image_base64 = models.TextField(blank=True)
    IMAGE_STATUT_CHOICES = [
        ("pas_commence", "Pas commencé"),
        ("en_cours", "En cours"),
        ("ok", "OK"),
        ("erreur", "Erreur"),
    ]

    image_statut = models.CharField(
        max_length=20,
        choices=IMAGE_STATUT_CHOICES,
        default="pas_commence"
    )
    image_tentatives = models.PositiveIntegerField(default=0)
    image_derniere_erreur = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Chapitre {self.numero} - {self.titre}"

