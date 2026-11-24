"""Give each Pages inventory a real, unique main commit before its deployment."""
import base64
import json
import os
import re
import subprocess

REPOSITORY = "nitinsharma47-ux/parv-ki-dhun-media"


def api(edge, payload=None):
    command = ["gh", "api", "repos/" + REPOSITORY + "/" + edge]
    if payload is not None:
        command += ["--method", "POST", "--input", "-"]
    result = subprocess.run(command, input=json.dumps(payload).encode() if payload is not None else None,
                            capture_output=True, timeout=45)
    if result.returncode:
        raise ValueError("Media deployment API failed; inspect main before another request")
    return json.loads(result.stdout) if result.stdout else {}


def request():
    identity = os.environ.get("DEPLOYMENT_REQUEST", "")
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY or not re.fullmatch(r"[0-9]+-[0-9]+", identity):
        raise ValueError("Deployment request must belong to the expected media workflow")
    base = api("git/ref/heads/main")["object"]["sha"]
    tree = api("git/commits/" + base)["tree"]["sha"]
    marker = json.dumps({"deployment_request": identity}, sort_keys=True) + "\n"
    blob = api("git/blobs", {"content": base64.b64encode(marker.encode()).decode(), "encoding": "base64"})
    updated = api("git/trees", {"base_tree": tree, "tree": [
        {"path": ".deployment.json", "mode": "100644", "type": "blob", "sha": blob["sha"]}]})
    commit = api("git/commits", {"message": "Refresh temporary media inventory " + identity,
                                "tree": updated["sha"], "parents": [base]})["sha"]
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("Invalid deployment commit")
    # PATCH with force:false refuses a concurrent update instead of replacing it.
    result = subprocess.run(["gh", "api", "repos/" + REPOSITORY + "/git/refs/heads/main",
                             "--method", "PATCH", "--input", "-"],
                            input=json.dumps({"sha": commit, "force": False}).encode(),
                            capture_output=True, timeout=45)
    if result.returncode or api("git/ref/heads/main")["object"]["sha"] != commit:
        raise ValueError("Media main changed; no deployment dispatched")
    api("actions/workflows/site.yml/dispatches", {"ref": "main", "inputs": {"build_commit": commit}})
    print(json.dumps({"deployment_commit": commit, "request": identity}))
    return commit


if __name__ == "__main__":
    try:
        request()
    except (ValueError, KeyError, TypeError, OSError, subprocess.TimeoutExpired):
        print("Media deployment request failed; retain current files and inspect main.")
        raise SystemExit(2) from None
