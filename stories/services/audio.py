import os
from gtts import gTTS

def texte_vers_audio_mp3(texte: str, langue: str, chemin_mp3: str):
    if not texte:
        return

    dossier = os.path.dirname(chemin_mp3)
    os.makedirs(dossier, exist_ok=True)

    tts = gTTS(text=texte, lang=langue)
    tts.save(chemin_mp3)
