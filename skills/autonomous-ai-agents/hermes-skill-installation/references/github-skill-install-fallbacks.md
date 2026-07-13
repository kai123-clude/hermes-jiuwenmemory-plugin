# GitHub Skill Install Fallbacks

This note captures a repeatable workaround for installing skills from GitHub when `hermes skills install OWNER/REPO --force` cannot fetch the identifier.

## Pattern

1. Try native install first with `--yes` in TUI sessions.
2. If it fails, locate `SKILL.md` by checking a local clone, GitHub contents API, raw URL, or codeload zip.
3. Copy or decode only `SKILL.md` into `~/.hermes/skills/<name>/SKILL.md` for the active profile.
4. Verify file size, CLI visibility, and `skill_view` loading.

## Empty Skill File Trap

A failed shell paste can create an empty `~/.hermes/skills/<name>/SKILL.md`. Hermes may still list the skill because the directory/file exists. Always run:

```bash
wc -c ~/.hermes/skills/<name>/SKILL.md
```

A size of `0` means the skill is not installed, even if `hermes skills list` shows it.

## Local Clone Repair

If the user cloned the repo manually, this is the fastest repair:

```bash
mkdir -p ~/.hermes/skills/<name>
cp /path/to/repo/SKILL.md ~/.hermes/skills/<name>/SKILL.md
wc -c ~/.hermes/skills/<name>/SKILL.md
hermes skills list | grep -i <name>
```

Then load with `skill_view(name="<name>")`.

## Codeload Zip Repair

When GitHub API or raw URLs are rate-limited, blocked, or unstable, `codeload.github.com` may still work:

```bash
curl -fL 'https://codeload.github.com/OWNER/REPO/zip/refs/heads/main' -o /tmp/REPO-main.zip
python3 - <<'PY'
import os, zipfile
zip_path = '/tmp/REPO-main.zip'
name = 'REPO'
with zipfile.ZipFile(zip_path) as z:
    skill = [n for n in z.namelist() if n.endswith('/SKILL.md') or n == 'SKILL.md'][0]
    content = z.read(skill).decode('utf-8')
out_dir = os.path.expanduser(f'~/.hermes/skills/{name}')
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, 'SKILL.md'), 'w', encoding='utf-8') as f:
    f.write(content)
print(os.path.join(out_dir, 'SKILL.md'), len(content.encode('utf-8')))
PY
```

Python's `zipfile` avoids requiring the host to have `unzip` installed.