"""Build a public media-only Pages site; platform credentials are never required."""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

REPOSITORY = "nitinsharma47-ux/parv-ki-dhun-media"
LIMIT = 32 * 1024 * 1024
SITE_LIMIT = 128 * 1024 * 1024


def validate_release(release):
    tag = release.get("tag_name", "")
    if not re.fullmatch(r"media-[a-f0-9]{64}", tag):
        raise ValueError("Unexpected release in media repository")
    assets = release.get("assets", [])
    sha = tag[6:]
    if (release.get("draft") or release.get("prerelease") is not True or len(assets) != 1
            or assets[0].get("name") != sha + ".mp4"
            or not isinstance(assets[0].get("size"), int) or not 0 < assets[0]["size"] <= LIMIT
            or assets[0].get("state") != "uploaded"):
        raise ValueError("Public release must contain exactly one bounded, hash-named MP4")
    return sha, assets[0]["size"]


def gh(args):
    result = subprocess.run(["gh", *args], capture_output=True, timeout=90)
    if result.returncode:
        raise ValueError("Public media could not be read; no API output displayed")
    return result.stdout


def build():
    deployment = {
        "source_commit": os.environ.get("GITHUB_SHA", ""),
        "workflow_run": os.environ.get("GITHUB_RUN_ID", ""),
        "attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""),
    }
    if (os.environ.get("GITHUB_REPOSITORY") != REPOSITORY
            or not re.fullmatch(r"[a-f0-9]{40}", deployment["source_commit"])
            or not re.fullmatch(r"[0-9]{1,30}", deployment["workflow_run"])
            or not re.fullmatch(r"[1-9][0-9]{0,5}", deployment["attempt"])):
        raise ValueError("Media builds require the approved repository and a valid workflow context")
    releases = json.loads(gh(["api", f"repos/{REPOSITORY}/releases?per_page=10"]))
    if not isinstance(releases, list) or len(releases) > 8:
        raise ValueError("Media site supports at most eight pending video files")
    selected = sorted(validate_release(row) for row in releases)
    if len({sha for sha, _ in selected}) != len(selected):
        raise ValueError("Conflicting media releases")
    if sum(size for _, size in selected) > SITE_LIMIT:
        raise ValueError("Media site exceeds 128 MiB")
    target = Path("public")
    target.mkdir(exist_ok=False)
    for sha, size in selected:
        path = target / (sha + ".mp4")
        gh(["release", "download", "media-" + sha, "--repo", REPOSITORY,
            "--pattern", path.name, "--output", str(path)])
        if path.stat().st_size != size or hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise ValueError("Public media digest differs from release name")
    (target / "index.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="robots" content="noindex"><title>Parv Ki Dhun media</title>'
        '<p>Temporary video delivery for Parv Ki Dhun.</p></html>', encoding="utf-8")
    (target / ".nojekyll").touch()
    (target / "manifest.json").write_text(json.dumps({
        "schema_version": 1, "deployment": deployment,
        "videos": [{"sha256": sha, "bytes": size} for sha, size in selected],
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(selected)} temporary videos; {sum(s for _, s in selected)} bytes.")


if __name__ == "__main__":
    try:
        build()
    except (ValueError, OSError, subprocess.TimeoutExpired):
        print("Media site build failed; previous deployment is retained.")
        raise SystemExit(2) from None
