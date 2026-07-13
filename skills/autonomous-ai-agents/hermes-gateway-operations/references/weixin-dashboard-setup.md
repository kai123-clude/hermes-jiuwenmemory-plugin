# Weixin Dashboard Setup Notes

Session-derived recipe for personal Weixin (WeChat) gateway setup in Hermes Dashboard/WSL.

## Preconditions

- Load the bundled `hermes-agent` skill and check official docs/CLI help.
- Confirm Hermes path/version and config locations:
  ```bash
  which hermes
  hermes --version
  hermes config path
  hermes config env-path
  ```
- Confirm Weixin dependencies in the Hermes venv:
  ```bash
  cd ~/.hermes/hermes-agent
  venv/bin/python - <<'PY'
  import importlib.util
  from gateway.platforms.weixin import check_weixin_requirements
  for name in ['aiohttp', 'cryptography', 'qrcode', 'PIL']:
      print(name, bool(importlib.util.find_spec(name)))
  print('check_weixin_requirements', check_weixin_requirements())
  PY
  ```
- If QR rendering support is missing, install:
  ```bash
  ~/.hermes/hermes-agent/venv/bin/python -m pip install 'qrcode[pil]'
  ```

## QR Login Without Fragile Menu Automation

If `hermes gateway setup` menu automation lands on the wrong platform in a pseudo-terminal, call the adapter directly:

```python
import asyncio, os
from pathlib import Path
from gateway.platforms.weixin import qr_login
from hermes_constants import get_hermes_home

ENV = Path(get_hermes_home()) / '.env'

def read_env():
    data = {}
    if ENV.exists():
        for line in ENV.read_text(errors='replace').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k, v = line.split('=', 1)
                data[k] = v
    return data

def write_env(updates):
    lines, seen = [], set()
    if ENV.exists():
        for line in ENV.read_text(errors='replace').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k = line.split('=', 1)[0]
                if k in updates:
                    lines.append(f'{k}={updates[k]}')
                    seen.add(k)
                else:
                    lines.append(line)
            else:
                lines.append(line)
    for k, v in updates.items():
        if k not in seen:
            lines.append(f'{k}={v}')
    ENV.write_text('\n'.join(lines).rstrip() + '\n')

async def main():
    creds = await qr_login(str(get_hermes_home()))
    if not creds:
        return
    current = read_env()
    updates = {
        'WEIXIN_ACCOUNT_ID': creds.get('account_id', ''),
        'WEIXIN_TOKEN': creds.get('token', ''),
        'WEIXIN_CDN_BASE_URL': current.get('WEIXIN_CDN_BASE_URL') or 'https://novac2c.cdn.weixin.qq.com/c2c',
        'WEIXIN_DM_POLICY': 'pairing',
        'WEIXIN_ALLOW_ALL_USERS': 'false',
        'WEIXIN_ALLOWED_USERS': '',
        'WEIXIN_GROUP_POLICY': 'disabled',
        'WEIXIN_GROUP_ALLOWED_USERS': '',
    }
    if creds.get('base_url'):
        updates['WEIXIN_BASE_URL'] = creds['base_url']
    if creds.get('user_id'):
        updates['WEIXIN_HOME_CHANNEL'] = creds['user_id']
    write_env(updates)

asyncio.run(main())
```

During QR display, generate a PNG attachment from the latest QR URL and also provide the raw URL. Avoid relying only on data URI inline rendering because long single-line assistant messages can be brittle.

## Persistence

On WSL with systemd available:

```bash
hermes gateway install --force --start-now --start-on-login
hermes gateway status
```

Verify Weixin connected in `~/.hermes/logs/gateway.log`:

```text
Connecting to weixin...
[Weixin] Connected account=... base=https://ilinkai.weixin.qq.com
✓ weixin connected
Gateway running with 1 platform(s)
```

## Outbound Test Pitfall

`hermes send --list weixin` may show no targets before channel discovery is populated. Direct sends to `WEIXIN_HOME_CHANNEL` can still fail with iLink `sendmessage rate limited` even after successful login and gateway connection. Do not conclude the gateway is broken from that alone.

For a reliable conversation test, ask the user to send a message from WeChat to the iLink bot first. Once the gateway receives it, Weixin stores a `context_token` for that peer and replies are more likely to succeed.
