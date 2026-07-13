# Weixin Direct QR Login Reference

Use this when `hermes gateway setup` platform selection is unreliable in a PTY, Dashboard, or automated session. It bypasses the interactive menu and calls the built-in Weixin adapter directly.

## Preconditions

```bash
cd ~/.hermes/hermes-agent
venv/bin/python - <<'PY'
import importlib.util
from gateway.platforms.weixin import check_weixin_requirements
for name in ['aiohttp', 'cryptography', 'qrcode', 'PIL']:
    print(f'{name}:', 'installed' if importlib.util.find_spec(name) else 'missing')
print('check_weixin_requirements:', check_weixin_requirements())
PY
```

Install QR display support if missing:

```bash
~/.hermes/hermes-agent/venv/bin/python -m pip install 'qrcode[pil]'
```

## Direct Login And Env Write

Run from the Hermes source directory:

```bash
cd ~/.hermes/hermes-agent
venv/bin/python - <<'PY'
import asyncio
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
    lines = []
    seen = set()
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
    print('CREDS', {k: ('***' if k == 'token' else v) for k, v in (creds or {}).items()}, flush=True)
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
    print('WROTE_ENV', ENV, flush=True)

asyncio.run(main())
PY
```

## QR Presentation

The script prints both a terminal QR and a `https://liteapp.weixin.qq.com/q/...` URL. If a browser/Dashboard surface needs a PNG, generate one from the URL:

```bash
cd ~/.hermes/hermes-agent
venv/bin/python - <<'PY'
from pathlib import Path
import qrcode
url = 'PASTE_QR_URL_HERE'
out = Path('/mnt/c/Users/LYH/hermes-weixin-qr-current.png')
qrcode.make(url).save(out)
print(out)
PY
```

For Dashboard, a media attachment/path is usually more stable than pasting a long `data:image/png;base64,...` line. Always include the QR URL as fallback.

## Verify Credentials

```bash
python3 - <<'PY'
from pathlib import Path
keys = ['WEIXIN_ACCOUNT_ID','WEIXIN_TOKEN','WEIXIN_BASE_URL','WEIXIN_CDN_BASE_URL','WEIXIN_DM_POLICY','WEIXIN_GROUP_POLICY','WEIXIN_HOME_CHANNEL']
vals = {}
for line in Path('/home/wzk/.hermes/.env').read_text(errors='replace').splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        k, v = line.split('=', 1)
        if k in keys:
            vals[k] = v
for k in keys:
    v = vals.get(k)
    if v is None:
        print(f'{k}: missing')
    elif 'TOKEN' in k:
        print(f'{k}: set ({len(v)} chars)')
    else:
        print(f'{k}: {v or "empty"}')
PY
```

## Start And Verify Gateway

Manual first-run verification:

```bash
hermes gateway run
```

Service installation on systemd-enabled Linux/WSL:

```bash
hermes gateway install --force --start-now --start-on-login
hermes gateway status
systemctl --user status hermes-gateway --no-pager
tail -80 ~/.hermes/logs/gateway.log
```

Expected log lines:

```text
Connecting to weixin...
[Weixin] Connected account=... base=https://ilinkai.weixin.qq.com
✓ weixin connected
Gateway running with 1 platform(s)
```
