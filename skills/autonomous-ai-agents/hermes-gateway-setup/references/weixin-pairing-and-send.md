# Weixin Pairing And Outbound Send Verification

Use this after Weixin QR login succeeds and the gateway connects, but outbound tests or user access do not behave as expected.

## Inbound First, Then Reply

Personal Weixin/iLink proactive sends can fail even with valid `WEIXIN_ACCOUNT_ID` and `WEIXIN_TOKEN`:

```text
iLink sendmessage rate limited; cooldown active for 30.0s
```

Treat this as a provider-side send constraint, not proof the gateway is disconnected. The reliable path is:

1. Ask the user to send a DM to the iLink bot from WeChat.
2. Confirm the gateway saw it:
   ```bash
   tail -160 ~/.hermes/logs/gateway.log | grep -i 'weixin\|pair\|context\|message\|denied\|allow\|received\|incoming'
   ```
   Look for:
   ```text
   [Weixin] inbound from=... type=dm media=0
   ```
3. Confirm a context token was written:
   ```bash
   find ~/.hermes/weixin/accounts -name '*context-tokens.json' -type f -printf '%p %s bytes\n'
   ```
4. Approve or allowlist the user, then reply/test again.

## Pairing UX Pitfall

`hermes pairing list` may show a short `Code` that is only the first 8 hex characters of the stored hash, not the original approval code. In that case, running:

```bash
hermes pairing approve weixin <displayed-code>
```

can fail with:

```text
Code '<CODE>' not found or expired for platform 'weixin'.
```

If this happens and the operator explicitly wants to approve the visible user, use the PairingStore API to approve the exact user id from `hermes pairing list`:

```bash
cd ~/.hermes/hermes-agent
venv/bin/python - <<'PY'
from gateway.pairing import PairingStore
uid = 'PASTE_WEIXIN_USER_ID_HERE'
store = PairingStore()
with store._lock:
    store._approve_user('weixin', uid, uid)
    pending_path = store._pending_path('weixin')
    pending = store._load_json(pending_path)
    for key, value in list(pending.items()):
        if isinstance(value, dict) and value.get('user_id') == uid:
            del pending[key]
    store._save_json(pending_path, pending)
print('approved', store.is_approved('weixin', uid))
PY
hermes pairing list
```

This is a workaround for the hashed-code display/approval mismatch; do not use it to approve users the operator has not explicitly identified.

## Direct Send Probe

The generic `hermes send --to weixin:<id>` path may fail target resolution before channel discovery is populated. For a low-level Weixin delivery probe, call the adapter helper directly after loading `.env`:

```bash
cd ~/.hermes/hermes-agent
venv/bin/python - <<'PY'
import asyncio, json, os
from pathlib import Path
from gateway.platforms.weixin import send_weixin_direct

for line in Path('/home/wzk/.hermes/.env').read_text(errors='replace').splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        key, value = line.split('=', 1)
        os.environ.setdefault(key, value)

chat_id = os.environ.get('WEIXIN_HOME_CHANNEL')
message = 'Hermes Weixin delivery test.'

async def main():
    result = await send_weixin_direct(extra={}, token=None, chat_id=chat_id, message=message)
    print(json.dumps(result, ensure_ascii=False, indent=2))

asyncio.run(main())
PY
```

If this returns rate limited, get an inbound message/context token first and ensure the user is approved before retrying.

## Restart Approvals

Restarting the gateway can trigger command approval in interactive Hermes sessions. If approval times out, do not loop or bypass it. Tell the user the exact command to approve or run manually:

```bash
hermes gateway restart
```
