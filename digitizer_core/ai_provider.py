"""Opt-in image editing. Credentials stay in environment; no retries or fallback."""
import base64
from datetime import datetime, timezone
from io import BytesIO
import os
from pathlib import Path
import time
from urllib.parse import urlparse
from PIL import Image
from .engine import save_json
from .masks import sha256


def decode_image(body, provider):
    if provider == "apiyi":
        items = body.get("data", [])
        if not items or not items[0].get("b64_json"):
            raise ValueError("Expected inline b64_json image; no remote URL is fetched.")
        encoded = items[0]["b64_json"]
    else:
        parts = [p for c in body.get("candidates", []) for p in c.get("content", {}).get("parts", [])]
        images = [p.get("inlineData", p.get("inline_data", {})) for p in parts]
        encoded = next((p["data"] for p in images if p.get("data")), None)
        if not encoded:
            raise ValueError("Gemini returned no inline image.")
    raw = base64.b64decode(encoded.split("base64,", 1)[-1], validate=True)
    with Image.open(BytesIO(raw)) as im:
        im.verify()
    return raw


def edit(bundle, provider="apiyi", model=None, timeout=600):
    """Exactly one paid request; a failed/unknown result requires explicit rerun."""
    import requests
    bundle = Path(bundle)
    if (bundle / "generated.png").exists() or (bundle / "request.json").exists():
        raise ValueError("This bundle already has a request. Prepare a new bundle for a new paid run.")
    import json
    meta = json.loads((bundle / "bundle.json").read_text())
    for filename, field in [("prompt.txt", "prompt_sha256"), ("prepared.png", "prepared_sha256"), (meta["source_file"], "source_sha256")]:
        if sha256(bundle / filename) != meta[field]:
            raise ValueError("Prepared payload changed; create a fresh reviewed bundle.")
    prompt = (bundle / "prompt.txt").read_text(encoding="utf-8")
    image = bundle / "prepared.png"
    if provider == "apiyi":
        model = model or "gpt-image-2.5-vip"
        key = next((os.environ[k] for k in ("APIYI_API_KEY", "APIYI_KEY", "API_YI_KEY") if os.environ.get(k)), "")
        url = os.environ.get("APIYI_IMAGES_BASE_URL", "https://api.apiyi.com/v1").rstrip("/") + "/images/edits"
        headers = {"Authorization": "Bearer " + key}
        if model.startswith("gemini-"):
            url = os.environ.get("APIYI_GEMINI_BASE_URL", "https://api.apiyi.com/v1beta").rstrip("/") + "/models/" + model + ":generateContent"
    elif provider == "gemini":
        model = model or "gemini-3-pro-image-preview"
        key = os.environ.get("GEMINI_API_KEY", "")
        url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent"
        headers = {"x-goog-api-key": key}
    else:
        raise ValueError("Choose apiyi or gemini; there is no automatic provider fallback.")
    if not key:
        raise ValueError("Missing credential: " + ("APIYI_API_KEY" if provider == "apiyi" else "GEMINI_API_KEY"))
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query:
        raise ValueError("Image endpoint must be HTTPS, without credentials or query strings.")
    metadata = dict(provider=provider, model=model, endpoint=url, started_at=datetime.now(timezone.utc).isoformat(),
                    prompt_sha256=sha256(bundle / "prompt.txt"), input_sha256=sha256(image), status="started", attempts=1)
    save_json(bundle / "request.json", metadata)
    start = time.monotonic()
    try:
        if provider == "apiyi" and not model.startswith("gemini-"):
            with image.open("rb") as f:
                response = requests.post(url, headers=headers, files={"image": ("prepared.png", f, "image/png")},
                                         data=dict(model=model, prompt=prompt, size="1536x1024", response_format="b64_json"), timeout=timeout)
        else:
            body = {"contents": [{"parts": [{"text": prompt}, {"inlineData": {"mimeType": "image/png", "data": base64.b64encode(image.read_bytes()).decode()}}]}],
                    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": {"aspectRatio": "3:2", "imageSize": "2K"}}}
            response = requests.post(url, headers=headers, json=body, timeout=timeout)
        metadata["http_status"] = response.status_code
        if not response.ok:
            # Provider bodies may echo request/credential details; keep only status.
            raise ValueError(f"Image service HTTP {response.status_code}; no image saved and no retry attempted.")
        raw = decode_image(response.json(), "gemini" if model.startswith("gemini-") else provider)
        # Decode and normalize without resampling; original response hash retained.
        import hashlib
        metadata["response_image_sha256"] = hashlib.sha256(raw).hexdigest()
        with Image.open(BytesIO(raw)) as im:
            metadata["output_size"] = list(im.size)
            im.convert("RGB").save(bundle / "generated.png")
        metadata.update(status="completed", output_sha256=sha256(bundle / "generated.png"))
        save_json(bundle / "review.draft.json", dict(reviewed=False,review_note="",source_sha256=meta["source_sha256"],generated_sha256=metadata["output_sha256"],anchor_pairs=[],note="Inspect both images; measure at least four matching landmarks spanning the plot. No size-based scaling."))
    except Exception as exc:
        metadata.update(status="failed_or_unknown", error_type=type(exc).__name__)
        raise ValueError(f"Image edit failed ({type(exc).__name__}); see request.json for HTTP status. No fallback or retry.") from None
    finally:
        metadata["elapsed_seconds"] = round(time.monotonic() - start, 3)
        save_json(bundle / "request.json", metadata)
    return metadata
