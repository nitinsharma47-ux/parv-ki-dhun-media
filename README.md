# Parv Ki Dhun temporary media

This public repository hosts only approved video exports needed by Buffer's API.
The application, source evidence, narration inputs and platform credentials stay
in the separate private source repository. No platform secret is needed here.

Each prerelease `media-SHA256` contains exactly one `SHA256.mp4` export, at most
32 MiB. The site verifies every file before deploying a direct, stable public URL
on GitHub Pages. It holds at most eight files and 128 MiB. A release deletion
rebuilds the site without that file after the private publication ledger confirms
every required destination. Files are not committed to Git history. Pages build
artifacts expire after one day. GitHub/CDN caching may outlast removal; this is
URL withdrawal, not a guarantee of immediate erasure of every cache.

Enable Pages with **GitHub Actions** as its deployment source and allow `main` in
the `github-pages` environment. Release creation/deletion requests a separate
`workflow_dispatch` from `main`; the release job has repository-local
`actions: write` solely for that request. This avoids the observed
[release-event Pages delivery issue](https://github.com/actions/deploy-pages/issues/383).
The deploy job accepts only `workflow_dispatch` on `main`. Unrelated release
tags are ignored; a tag deployment allowance is unnecessary with this version.

Every build writes a public, nonsecret `manifest.json` containing its source
commit, workflow run/attempt and the hashes/sizes of its videos. After deployment,
`verify_site.py` waits at most three minutes for that exact inventory and fetches
each MP4 without credentials or redirects to check its digest. A green Pages
deployment without matching public delivery fails this verification. The private
publishing queue also checks the exact video bytes before sending its URL to
Buffer. Public URLs are retained until publication and the separate cleanup check.

Keep the repository
public on GitHub Free and platform credentials out of its secrets. The private
source runner needs a separate token restricted to this repository with Contents
read/write. Its one-time setup also needs an owner to enable Pages and install
this workflow. No billing upgrade or paid service is used.

Deployment source: `deploy/media-site/` in the private application. Installation
and the first public URL remain unverified until recorded in its running guide.
