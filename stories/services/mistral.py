import os
import json
from mistralai import Mistral  # SDK officiel Mistral


def generer_histoire(prenom_enfant, age, mots_cles, ton):
    """
    Appelle l'API Mistral et renvoie un dict Python:
    {
      "morale": "...",
      "chapitres": [
        {"numero": 1, "titre": "...", "texte": "..."},
        ...
      ]
    }
    """

    cle_api = os.environ.get("MISTRAL_API_KEY")
    if not cle_api:
        raise ValueError("MISTRAL_API_KEY manquante (vérifie ton fichier .env)")

    client = Mistral(api_key=cle_api)

    consigne = f"""
Tu es un conteur pour enfant.
Génère une histoire en français pour {prenom_enfant} ({age} ans).
Mots-clés: {mots_cles}
Ton: {ton}

IMPORTANT :
- Réponds UNIQUEMENT avec un JSON valide.
- Aucun texte avant/après.
- Minimum 4 chapitres.

Format JSON attendu :
{{
  "morale": "texte de la morale",
  "chapitres": [
    {{"numero": 1, "titre": "Titre du chapitre 1", "texte": "Texte du chapitre 1"}},
    {{"numero": 2, "titre": "Titre du chapitre 2", "texte": "Texte du chapitre 2"}},
    {{"numero": 3, "titre": "Titre du chapitre 3", "texte": "Texte du chapitre 3"}},
    {{"numero": 4, "titre": "Titre du chapitre 4", "texte": "Texte du chapitre 4"}}
  ]
}}
""".strip()

    reponse = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": consigne}],
        response_format={"type": "json_object"},
    )

    contenu = reponse.choices[0].message.content

    if isinstance(contenu, list): # cas où Mistral renvoie une liste de parties
        texte = "".join(part.get("text", "") for part in contenu)
    else:
        texte = contenu

    texte = (texte or "").strip()
    texte = texte.replace("```json", "").replace("```", "").strip()

    if not texte:
        raise ValueError("Réponse Mistral vide (impossible de parser le JSON)")

    return json.loads(texte)
