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

Enable Pages with **GitHub Actions** as its deployment source. Keep this repository
public on GitHub Free and platform credentials out of its secrets. The private
source runner needs a separate token restricted to this repository with Contents
read/write. Its one-time setup also needs an owner to enable Pages and install
this workflow. No billing upgrade or paid service is used.

Deployment source: `deploy/media-site/` in the private application. Installation
and the first public URL remain unverified until recorded in its running guide.
