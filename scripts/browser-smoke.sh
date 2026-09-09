#!/usr/bin/env bash
# Requires the API on localhost:8000 and UI on localhost:3000.
set -euo pipefail
npx --yes --package @playwright/cli@0.1.19 playwright-cli -s=sentinel-ci open http://localhost:3000/register
trap 'npx --yes --package @playwright/cli@0.1.19 playwright-cli -s=sentinel-ci close' EXIT
npx --yes --package @playwright/cli@0.1.19 playwright-cli -s=sentinel-ci run-code --filename=scripts/browser_smoke.js
npx --yes --package @playwright/cli@0.1.19 playwright-cli -s=sentinel-ci dialog-accept
npx --yes --package @playwright/cli@0.1.19 playwright-cli -s=sentinel-ci run-code --filename=scripts/browser_smoke_finish.js
npx --yes --package @playwright/cli@0.1.19 playwright-cli -s=sentinel-ci snapshot | python3 -c 'import sys; assert "Page URL: http://localhost:3000/login" in sys.stdin.read()'
echo "BROWSER_SMOKE_PASS: registration, login, queued upload, preview, streaming UI, delete, logout"
