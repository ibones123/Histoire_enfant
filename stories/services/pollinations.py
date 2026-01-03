import base64
import re
import urllib.parse
import requests


def generer_image_base64(prompt: str, seed: int = 1) -> str:
    """
    Renvoie une data URL base64 (affichable directement dans <img src="...">)
    Exemple: data:image/jpeg;base64,iVBORw0...
    """
    return _generer_pollinations_image(prompt, seed)


def _generer_pollinations_image(prompt: str, seed: int) -> str:
    # Nettoyage léger
    clean_prompt = re.sub(r"[^\w\s,.-]", "", prompt).strip()

    # On coupe si trop long (Pollinations peut bug si prompt énorme)
    if len(clean_prompt) > 450:
        clean_prompt = clean_prompt[:450].rsplit(" ", 1)[0] + "..."

    # URL Pollinations (avec seed)
    url = (
        "https://image.pollinations.ai/prompt/"
        f"{urllib.parse.quote_plus(clean_prompt)}"
        f"?width=768&height=768&seed={seed}&nologo=true"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, timeout=60, headers=headers, allow_redirects=True)

    if response.status_code != 200 or len(response.content) < 500:
        raise Exception(f"Pollinations n'a pas renvoyé d'image (HTTP {response.status_code})")

    content_type = (response.headers.get("Content-Type") or "").lower()
    if "image" not in content_type:
        raise Exception("Pollinations n'a pas renvoyé une image (Content-Type invalide)")

    mime_type = content_type.split(";")[0] if content_type else "image/jpeg"
    image_b64 = base64.b64encode(response.content).decode("utf-8")

    return f"data:{mime_type};base64,{image_b64}"
