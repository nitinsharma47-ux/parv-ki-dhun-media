"""Verify actual Pages delivery independently of its deployment status."""
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://nitinsharma47-ux.github.io/parv-ki-dhun-media/"
FILE_LIMIT = 32 * 1024 * 1024
VERIFY_SECONDS = 180
MAX_ATTEMPTS = 18


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch(name, limit, timeout):
    request = urllib.request.Request(BASE + name, headers={"User-Agent": "ParvKiDhun-Media/0.2"})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
        body = response.read(limit + 1)
        if response.status != 200 or len(body) > limit:
            raise ValueError("Unexpected public media response")
        return body


def verify(folder=Path("public")):
    expected = (folder / "manifest.json").read_bytes()
    manifest = json.loads(expected)
    videos = manifest.get("videos")
    if (manifest.get("schema_version") != 1 or len(expected) > 32768
            or not isinstance(videos, list) or len(videos) > 8):
        raise ValueError("Invalid media inventory")
    for video in videos:
        if (not re.fullmatch(r"[a-f0-9]{64}", video.get("sha256", ""))
                or type(video.get("bytes")) is not int or not 0 < video["bytes"] <= FILE_LIMIT):
            raise ValueError("Invalid media binding")
    if sum(video["bytes"] for video in videos) > 128 * 1024 * 1024:
        raise ValueError("Media inventory exceeds the site bound")
    deadline = time.monotonic() + VERIFY_SECONDS
    inventory_verified = False
    for attempt in range(MAX_ATTEMPTS):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            inventory_verified = fetch("manifest.json", 32768, min(20, remaining)) == expected
        except urllib.error.HTTPError as error:
            if error.code not in (404, 429, 500, 502, 503, 504):
                raise ValueError("Pages did not permit public delivery") from None
        except (urllib.error.URLError, OSError, TimeoutError):
            pass
        if inventory_verified:
            break
        remaining = deadline - time.monotonic()
        if attempt + 1 < MAX_ATTEMPTS and remaining > 0:
            time.sleep(min(10, remaining))
    if not inventory_verified:
        raise ValueError("Pages is still serving a different inventory; deployment unverified")
    for video in videos:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("Public media verification exceeded three minutes")
        body = fetch(video["sha256"] + ".mp4", FILE_LIMIT, min(30, remaining))
        if len(body) != video["bytes"] or hashlib.sha256(body).hexdigest() != video["sha256"]:
            raise ValueError("Pages delivered different video bytes")
    result = {"public_delivery_verified": True, "deployment": manifest["deployment"],
              "verified_videos": len(videos), "bytes": sum(video["bytes"] for video in videos)}
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    try:
        verify()
    except (ValueError, KeyError, TypeError, OSError, urllib.error.URLError):
        print("Public delivery verification failed; no platform publication should use this deployment.")
        raise SystemExit(2) from None
