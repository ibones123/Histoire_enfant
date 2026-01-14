from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch

from stories.models import Enfant, Histoire, Chapitre

# Create your tests here.


class TestAccounts(TestCase):

    def creer_user_et_login(self):
        user = User.objects.create_user(username="test", password="test1234")
        ok = self.client.login(username="test", password="test1234")
        self.assertTrue(ok)
        return user

    def test_inscription_page_ok(self):
        url = reverse("inscription")
        rep = self.client.get(url)
        self.assertEqual(rep.status_code, 200)

    def test_connexion_page_ok(self):
        url = reverse("connexion")
        rep = self.client.get(url)
        self.assertEqual(rep.status_code, 200)

    def test_dashboard_demande_login(self):
        url = reverse("dashboard")
        rep = self.client.get(url)
        # redirect vers login (302)
        self.assertEqual(rep.status_code, 302)

    def test_dashboard_ok_quand_connecte(self):
        self.creer_user_et_login()
        url = reverse("dashboard")
        rep = self.client.get(url)
        self.assertEqual(rep.status_code, 200)

    def test_ajouter_enfant(self):
        user = self.creer_user_et_login()

        url = reverse("ajouter_enfant")
        rep = self.client.post(url, {"prenom": "Ibo", "age": 6})
        self.assertEqual(rep.status_code, 302)

        enfant = Enfant.objects.get(parent=user)
        self.assertEqual(enfant.prenom, "Ibo")
        self.assertEqual(enfant.age, 6)


class TestHistoires(TestCase):

    def creer_user_enfant_et_login(self):
        user = User.objects.create_user(username="test", password="test1234")
        self.client.login(username="test", password="test1234")
        enfant = Enfant.objects.create(parent=user, prenom="Ibo", age=6)
        return user, enfant

    @patch("accounts.views.generer_histoire")
    def test_creer_histoire_cree_chapitres_et_redirect_generation(self, mock_generer_histoire):
        """
        On vérifie qu'on crée l'histoire + chapitres, puis redirection vers /generation/<id>/
        sans appeler la vraie API Mistral.
        """
        user, enfant = self.creer_user_enfant_et_login()

        mock_generer_histoire.return_value = {
            "morale": "Toujours croire en soi.",
            "chapitres": [
                {"numero": 1, "titre": "Chapitre 1", "texte": "Texte 1"},
                {"numero": 2, "titre": "Chapitre 2", "texte": "Texte 2"},
            ],
        }

        url = reverse("creer_histoire")
        rep = self.client.post(url, {"enfant_id": enfant.id, "titre": "nuage"})
        self.assertEqual(rep.status_code, 302)

        histoire = Histoire.objects.get(enfant=enfant)
        self.assertEqual(histoire.morale, "Toujours croire en soi.")
        self.assertEqual(Chapitre.objects.filter(histoire=histoire).count(), 2)

        self.assertIn(reverse("generation_histoire", args=[histoire.id]), rep["Location"])

    @patch("accounts.views.generer_image_base64")
    def test_api_generer_image_termine_quand_plus_rien_a_faire(self, mock_generer_image_base64):
        user, enfant = self.creer_user_enfant_et_login()

        histoire = Histoire.objects.create(enfant=enfant, titre="Test", morale="OK")
        Chapitre.objects.create(histoire=histoire, numero=1, titre="C1", texte="T1", image_base64="deja_ok")

        url = reverse("api_generer_image", args=[histoire.id])
        rep = self.client.get(url)
        self.assertEqual(rep.status_code, 200)
        self.assertJSONEqual(rep.content, {"termine": True})

    @patch("accounts.views.generer_image_base64")
    def test_api_generer_image_genere_une_image_sur_un_chapitre_vide(self, mock_generer_image_base64):
        user, enfant = self.creer_user_enfant_et_login()

        mock_generer_image_base64.return_value = "data:image/jpeg;base64,FAKE"

        histoire = Histoire.objects.create(enfant=enfant, titre="Test", morale="OK")
        chapitre = Chapitre.objects.create(histoire=histoire, numero=1, titre="C1", texte="T1", image_base64="")

        url = reverse("api_generer_image", args=[histoire.id])
        rep = self.client.get(url)
        self.assertEqual(rep.status_code, 200)

        chapitre.refresh_from_db()
        self.assertTrue(chapitre.image_base64.startswith("data:image"))
