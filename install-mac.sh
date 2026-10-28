#!/usr/bin/env bash
set -euo pipefail
# User-local official installer. Avoid Homebrew and sudo for the npm/runtime path.
prefix="$HOME/.local/share/mymind-runtime"
installer="$(mktemp -t mymind-installer.XXXXXX)"
trap 'rm -f "$installer"' EXIT
curl --fail --location --silent --show-error --proto '=https' --tlsv1.2 \
  https://openclaw.ai/install-cli.sh -o "$installer"
bash "$installer" --prefix "$prefix" --version 2026.10.8 --runtime-only --npm
"$prefix/bin/openclaw" --version
echo 'Installed. For this terminal and each new terminal, run:'
echo 'export PATH="$HOME/.local/share/mymind-runtime/bin:$PATH"'
