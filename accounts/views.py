import os

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import FileResponse, JsonResponse
from django.shortcuts import render, redirect

from django.http import JsonResponse
from stories.services.pollinations import generer_image_base64


from django.http import JsonResponse
from django.db.models import Q

from stories.models import Enfant, Histoire, Chapitre
from stories.services.mistral import generer_histoire
from stories.services.pollinations import generer_image_base64
from stories.services.audio import texte_vers_audio_mp3
from stories.services.traduction import traduire_texte

def extrait_pour_image(texte: str, max_chars: int = 260) -> str:
    if not texte:
        return ""
    texte = texte.replace("\n", " ").strip()
    if len(texte) > max_chars:
        texte = texte[:max_chars].rsplit(" ", 1)[0] + "..."
    return texte



def accueil(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "accounts/accueil.html")

from django.contrib.auth.models import User
from django.contrib.auth import login

def inscription(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if not username or not password1 or not password2:
            return render(request, "accounts/inscription.html", {"erreur": "Remplis tous les champs."})

        if password1 != password2:
            return render(request, "accounts/inscription.html", {"erreur": "Les mots de passe ne correspondent pas."})

        if User.objects.filter(username=username).exists():
            return render(request, "accounts/inscription.html", {"erreur": "Ce nom d'utilisateur est déjà pris."})

        user = User.objects.create_user(username=username, password=password1)
        login(request, user)
        return redirect("dashboard")

    return render(request, "accounts/inscription.html")



def connexion(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        utilisateur = authenticate(request, username=username, password=password)

        if utilisateur is not None:
            login(request, utilisateur)
            return redirect("dashboard")

        return render(request, "accounts/connexion.html", {"erreur": "Identifiants invalides."})

    return render(request, "accounts/connexion.html")


def deconnexion(request):
    logout(request)
    return redirect("accueil")




@login_required
def dashboard(request):
    enfants = Enfant.objects.filter(parent=request.user)
    histoires = Histoire.objects.filter(enfant__parent=request.user).order_by("-date_creation")

    return render(request, "accounts/dashboard.html", {
        "enfants": enfants,
        "histoires": histoires,
    })

@login_required
def ajouter_enfant(request):
    if request.method == "POST":
        prenom = request.POST.get("prenom")
        age = request.POST.get("age")

        if not prenom or not age:
            return render(request, "accounts/ajouter_enfant.html", {"erreur": "Prénom et âge obligatoires."})

        Enfant.objects.create(
            parent=request.user,
            prenom=prenom,
            age=int(age)
        )
        return redirect("dashboard")

    return render(request, "accounts/ajouter_enfant.html")


@login_required
def generation_histoire(request, histoire_id):
    histoire = Histoire.objects.get(id=histoire_id, enfant__parent=request.user)
    chapitres = Chapitre.objects.filter(histoire=histoire).order_by("numero")

    return render(request, "accounts/generation.html", {
        "histoire": histoire,
        "chapitres": chapitres,
    })




@login_required
def creer_histoire(request):
    enfants = Enfant.objects.filter(parent=request.user)

    if request.method == "POST":
        enfant_id = request.POST.get("enfant_id")
        titre = request.POST.get("titre")

        if not enfant_id or not titre:
            return render(request, "accounts/creer_histoire.html", {
                "enfants": enfants,
                "erreur": "Choisis un enfant et mets un titre."
            })

        enfant = Enfant.objects.get(id=enfant_id, parent=request.user)

        resultat = generer_histoire(
            prenom_enfant=enfant.prenom,
            age=enfant.age,
            mots_cles=titre,
            ton="doux"
        )

        histoire = Histoire.objects.create(
            enfant=enfant,
            titre=titre,
            morale=resultat.get("morale", "")
        )

        chapitres = resultat.get("chapitres", [])
        for ch in chapitres:
            Chapitre.objects.create(
                histoire=histoire,
                numero=ch.get("numero"),
                titre=ch.get("titre", ""),
                texte=ch.get("texte", ""),
                image_base64=""   
            )

        return redirect("generation_histoire", histoire_id=histoire.id)

    return render(request, "accounts/creer_histoire.html", {"enfants": enfants})

@login_required
def voir_histoire(request, histoire_id):
    histoire = Histoire.objects.get(id=histoire_id, enfant__parent=request.user)
    chapitres = Chapitre.objects.filter(histoire=histoire).order_by("numero")
    langue = request.GET.get("langue", "fr")

    if langue != "fr":
        histoire.titre = traduire_texte(histoire.titre, langue)
        histoire.morale = traduire_texte(histoire.morale, langue)

        for chapitre in chapitres:
            chapitre.titre = traduire_texte(chapitre.titre, langue)
            chapitre.texte = traduire_texte(chapitre.texte, langue)

    return render(request, "accounts/voir_histoire.html", {
        "histoire": histoire,
        "chapitres": chapitres,
        "langue": langue,

    })




@login_required
def audio_histoire(request, histoire_id):
    langue = request.GET.get("langue", "fr")
    if langue not in ["fr", "en", "es", "ar"]:
        langue = "fr"

    histoire = Histoire.objects.get(id=histoire_id, enfant__parent=request.user)
    chapitres = Chapitre.objects.filter(histoire=histoire).order_by("numero")

    titre = histoire.titre or ""
    morale = histoire.morale or ""

    if langue != "fr":
        titre = traduire_texte(titre, langue)
        morale = traduire_texte(morale, langue)

    texte_a_lire = f"{titre}. "

    for ch in chapitres:
        ch_titre = ch.titre or ""
        ch_texte = ch.texte or ""

        if langue != "fr":
            ch_titre = traduire_texte(ch_titre, langue)
            ch_texte = traduire_texte(ch_texte, langue)

        texte_a_lire += f"{ch_titre}. {ch_texte}. "

    if morale:
        texte_a_lire += f"{morale}."

    nom_fichier = f"histoire_{histoire_id}_{langue}.mp3"
    chemin_mp3 = os.path.join(settings.MEDIA_ROOT, "audio", nom_fichier)

    if not os.path.exists(chemin_mp3):
        texte_vers_audio_mp3(texte_a_lire, langue, chemin_mp3)

    return FileResponse(open(chemin_mp3, "rb"), content_type="audio/mpeg")


@login_required
def audio_chapitre(request, chapitre_id):
    langue = request.GET.get("langue", "fr")
    if langue not in ["fr", "en", "es", "ar"]:
        langue = "fr"

    chapitre = Chapitre.objects.get(
        id=chapitre_id,
        histoire__enfant__parent=request.user
    )

    titre = chapitre.titre
    texte = chapitre.texte

    if langue != "fr":
        titre = traduire_texte(titre, langue)
        texte = traduire_texte(texte, langue)

    texte_a_lire = f"{titre}. {texte}."

    nom_fichier = f"chapitre_{chapitre_id}_{langue}.mp3"
    chemin_mp3 = os.path.join(settings.MEDIA_ROOT, "audio", nom_fichier)

    if not os.path.exists(chemin_mp3):
        texte_vers_audio_mp3(texte_a_lire, langue, chemin_mp3)

    return FileResponse(open(chemin_mp3, "rb"), content_type="audio/mpeg")



MAX_TENTATIVES_IMAGE = 3

@login_required
def api_generer_image(request, histoire_id):
    histoire = Histoire.objects.get(id=histoire_id, enfant__parent=request.user)

    # 1) On cherche un chapitre "à faire"
    # - pas d'image
    # - pas déjà ok
    # - tentatives < MAX
    chapitre = (Chapitre.objects
        .filter(histoire=histoire)
        .filter(Q(image_base64="") | Q(image_base64__isnull=True))
        .exclude(image_statut="ok")
        .filter(image_tentatives__lt=MAX_TENTATIVES_IMAGE)
        .order_by("numero")
        .first()
    )

    # 2) Si aucun chapitre à faire, alors c'est terminé (ou bien il reste des erreurs mais on ne bloque pas)
    if chapitre is None:
        total = Chapitre.objects.filter(histoire=histoire).count()
        ok_count = Chapitre.objects.filter(histoire=histoire, image_statut="ok").count()
        erreur_count = Chapitre.objects.filter(histoire=histoire, image_statut="erreur").count()

        return JsonResponse({
            "termine": True,
            "total": total,
            "ok": ok_count,
            "erreur": erreur_count,
        })

    # 3) On marque "en cours" + on incrémente les tentatives
    chapitre.image_statut = "en_cours"
    chapitre.image_tentatives += 1
    chapitre.save()

    extrait = extrait_pour_image(chapitre.texte)
    prenom = histoire.enfant.prenom
    age = histoire.enfant.age

    prompt_image = (
        "Illustration de livre pour enfant, dessin doux, couleurs pastel, style conte. "
        "Une seule scène claire, personnages mignons, lumière chaleureuse, décor simple. "
        "Pas de texte, pas de watermark, pas de logo. "
        f"Personnage principal: un enfant nommé {prenom}, environ {age} ans. "
        f"Scène à illustrer: {chapitre.titre}. {extrait}"
    )

    seed = chapitre.id

    try:
        chapitre.image_base64 = generer_image_base64(prompt_image, seed=seed)
        chapitre.image_statut = "ok"
        chapitre.image_derniere_erreur = ""
        chapitre.save()

        total = Chapitre.objects.filter(histoire=histoire).count()
        ok_count = Chapitre.objects.filter(histoire=histoire, image_statut="ok").count()
        erreur_count = Chapitre.objects.filter(histoire=histoire, image_statut="erreur").count()

        return JsonResponse({
            "termine": False,
            "chapitre_ok": chapitre.numero,
            "total": total,
            "ok": ok_count,
            "erreur": erreur_count,
        })

    except Exception as e:
        # IMPORTANT : on ne reste pas bloqué → on marque le chapitre en erreur si on a atteint la limite
        msg = str(e)

        if chapitre.image_tentatives >= MAX_TENTATIVES_IMAGE:
            chapitre.image_statut = "erreur"
        else:
            chapitre.image_statut = "pas_commence"  # on pourra retenter encore (jusqu'à MAX)

        chapitre.image_derniere_erreur = msg
        chapitre.save()

        total = Chapitre.objects.filter(histoire=histoire).count()
        ok_count = Chapitre.objects.filter(histoire=histoire, image_statut="ok").count()
        erreur_count = Chapitre.objects.filter(histoire=histoire, image_statut="erreur").count()

        return JsonResponse({
            "termine": False,
            "erreur": msg,
            "chapitre": chapitre.numero,
            "tentatives": chapitre.image_tentatives,
            "max_tentatives": MAX_TENTATIVES_IMAGE,
            "total": total,
            "ok": ok_count,
            "erreur_count": erreur_count,
        }, status=200)
