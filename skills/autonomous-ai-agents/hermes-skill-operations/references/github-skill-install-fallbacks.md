# GitHub Skill Install Fallbacks

This reference captures a concrete pattern for installing a skill when `hermes skills install owner/repo` cannot resolve the source and raw GitHub fetches are unreliable.

## Symptoms

- `hermes skills install <owner>/<repo> --force` prints `Could not fetch '<owner>/<repo>' from any source`.
- The GitHub contents API for the repository root works and shows a root `SKILL.md`.
- `raw.githubusercontent.com` may time out or otherwise fail in the current network path.
- A failed manual paste can still leave `~/.hermes/skills/<name>/SKILL.md` as a zero-byte file, while `hermes skills list` shows the skill as enabled.

## Recovery Command

Use the GitHub contents API, decode the base64 `content` field, and write the result into the skill directory:

```bash
mkdir -p ~/.hermes/skills/<skill-name> && curl -fsSL 'https://api.github.com/repos/<owner>/<repo>/contents/SKILL.md?ref=main' | python3 -c 'import sys,json,base64; print(base64.b64decode(json.load(sys.stdin)["content"]).decode("utf-8"))' > ~/.hermes/skills/<skill-name>/SKILL.md
```

For `conorbronsdon/avoid-ai-writing`, the concrete command is:

```bash
mkdir -p ~/.hermes/skills/avoid-ai-writing && curl -fsSL 'https://api.github.com/repos/conorbronsdon/avoid-ai-writing/contents/SKILL.md?ref=main' | python3 -c 'import sys,json,base64; print(base64.b64decode(json.load(sys.stdin)["content"]).decode("utf-8"))' > ~/.hermes/skills/avoid-ai-writing/SKILL.md
```

## Verification

```bash
wc -c ~/.hermes/skills/<skill-name>/SKILL.md
hermes skills list | grep -i '<skill-name>'
```

If `wc -c` prints `0`, the skill only exists as a placeholder. Re-run the single-line recovery command carefully. When tool access permits, also verify with `skill_view(name='<skill-name>')` and confirm the content is non-empty.