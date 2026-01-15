from mistralai import Mistral
import os

def traduire_texte(texte: str, langue: str) -> str:
    if not texte:
        return ""

    cle_api = os.environ.get("MISTRAL_API_KEY")
    if not cle_api:
        return texte 

    client = Mistral(api_key=cle_api)

    langues_ok = {
        "fr": "français",
        "en": "anglais",
        "es": "espagnol",
        "ar": "arabe"
    }
    if langue not in langues_ok:
        return texte

    langue_nom = langues_ok[langue]

    consigne = f"""
Traduis ce texte en {langue_nom}.
Règles :
- Garde le sens, reste naturel.
- Ne rajoute rien.
- Réponds uniquement avec la traduction.

Texte :
{texte}
""".strip()

    reponse = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": consigne}],
    )

    contenu = reponse.choices[0].message.content
    return contenu.strip() if contenu else texte
