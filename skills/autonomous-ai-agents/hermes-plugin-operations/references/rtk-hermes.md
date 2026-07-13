# RTK Hermes Plugin Setup Notes

Use this reference when enabling `rtk-hermes`, the Hermes plugin that rewrites terminal commands through the external `rtk` CLI.

## Verified Checks

- Repo/package: `rtk-hermes`
- Hermes plugin entry point: `rtk-rewrite = "rtk_hermes"`
- Hermes config enablement:
  ```yaml
  plugins:
    enabled:
      - rtk-rewrite
  ```
- Python package must be installed into the Hermes Python environment, not system Python:
  ```bash
  HERMES_PY="$HOME/.hermes/hermes-agent/venv/bin/python"
  "$HERMES_PY" -m pip install --upgrade rtk-hermes
  "$HERMES_PY" - <<'PY'
from importlib.metadata import distribution, entry_points
print(distribution('rtk-hermes').version)
print([(ep.name, ep.value) for ep in entry_points(group='hermes_agent.plugins') if ep.name == 'rtk-rewrite'])
PY
  ```
- Runtime executable must also exist:
  ```bash
  command -v rtk
  rtk --version
  rtk rewrite "git status"
  ```

## WSL / Network Fallback For RTK CLI

If the official installer stalls while downloading the GitHub release asset, avoid unrelated same-name packages:

- npm `rtk` is a release-tool package from `cliffano/rtk`, not `rtk-ai/rtk`.
- PyPI `RTk` is a GPIO library, not `rtk-ai/rtk`.
- crates.io `rtk` may not track the current `rtk-ai/rtk` CLI release.

A verified fallback is to download the release asset through a reachable GitHub mirror, download `checksums.txt`, verify SHA-256, and install to `~/.local/bin`:

```bash
set -euo pipefail
version='v0.43.0'
url_base="https://gh.llkk.cc/https://github.com/rtk-ai/rtk/releases/download/${version}"
tmp=$(mktemp -d)
asset='rtk-x86_64-unknown-linux-musl.tar.gz'
archive="$tmp/$asset"
checksums="$tmp/checksums.txt"

curl -fL --connect-timeout 20 --max-time 180 "$url_base/$asset" -o "$archive"
curl -fL --connect-timeout 20 --max-time 60 "$url_base/checksums.txt" -o "$checksums"

expected=$(awk -v a="$asset" '$2 == a {print $1}' "$checksums")
actual=$(sha256sum "$archive" | awk '{print $1}')
test -n "$expected"
test "$expected" = "$actual"

tar -tzf "$archive" | grep -qE '^/|(^|/)\.\.(/|$)' && { echo 'unsafe archive paths'; exit 1; } || true
tar -xzf "$archive" -C "$tmp"
mkdir -p "$HOME/.local/bin"
install -m 755 "$tmp/rtk" "$HOME/.local/bin/rtk"
"$HOME/.local/bin/rtk" --version
```

For `v0.43.0` Linux x86_64 musl, the observed checksum was:

```text
ff8a1e7766496e175291a85aeca1dc97c9ff6df33e51e5893d1fbc78fea2a609  rtk-x86_64-unknown-linux-musl.tar.gz
```

Always prefer the current upstream `checksums.txt` over hardcoding this value for newer versions.

## Final Verification

After package, CLI, and config are in place, start a new Hermes process:

```bash
PATH="$HOME/.local/bin:$PATH" hermes chat -q '只回答 OK' -Q
```

A currently running TUI session generally needs restart before it loads a newly enabled plugin.
