---
name: hermes-skill-installation
description: Install, repair, and verify Hermes Agent skills from hub identifiers, GitHub repositories, direct SKILL.md files, local clones, and archive fallbacks.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, skills, installation, troubleshooting, github]
    related_skills: [hermes-agent, hermes-agent-skill-authoring]
---

# Hermes Skill Installation

Use this skill when the user asks to install a Hermes skill, especially from a GitHub-style identifier such as `owner/repo`, a direct `SKILL.md` URL, or a local clone. The goal is a usable skill in the active profile's skill library, verified by both the CLI and `skill_view`.

## Default Path

1. Try the native installer first:

```bash
hermes skills install OWNER/REPO --force --yes
```

2. Verify immediately:

```bash
hermes skills list | grep -i NAME
```

3. If the installer succeeds, load it with `skill_view(name="NAME")` before reporting success.

## GitHub Fallbacks

If the native installer cannot fetch the identifier, install from the repo's `SKILL.md` manually.

Preferred fallback order:

1. Check whether the user already cloned the repository. Common locations in WSL are the current working directory and `/mnt/c/Users/<WindowsUser>/REPO`.
2. If a clone exists, copy its `SKILL.md` into the active profile skill directory:

```bash
mkdir -p ~/.hermes/skills/NAME
cp /path/to/repo/SKILL.md ~/.hermes/skills/NAME/SKILL.md
```

3. If there is no clone, try GitHub contents API and decode base64:

```bash
mkdir -p ~/.hermes/skills/NAME
curl -fsSL 'https://api.github.com/repos/OWNER/REPO/contents/SKILL.md?ref=main' \
  | python3 -c 'import sys,json,base64; print(base64.b64decode(json.load(sys.stdin)["content"]).decode("utf-8"))' \
  > ~/.hermes/skills/NAME/SKILL.md
```

4. If raw/API routes are unreliable, use codeload zip and Python's standard library instead of relying on `unzip`:

```bash
curl -fL 'https://codeload.github.com/OWNER/REPO/zip/refs/heads/main' -o /tmp/REPO-main.zip
python3 - <<'PY'
import os, zipfile
repo = 'REPO'
name = 'NAME'
zip_path = f'/tmp/{repo}-main.zip'
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

## Repository Inspection and Adaptation

A GitHub repository is not necessarily one installable skill. Before copying anything:

1. Inspect the repository tree and README. Distinguish a single root skill from a nested skill, a multi-skill catalog, or a CLI/runtime that merely distributes skills.
2. Locate every `SKILL.md`; derive the install unit from the containing directory and frontmatter rather than the repository name.
3. Review supporting scripts and configs for client-specific paths (`~/.claude/skills`, macOS app bundles), placeholder secrets, required runtimes, and code defects.
4. Prefer selective installation over importing a large catalog. Bulk catalogs can create duplicate names, conflicting triggers, unnecessary context load, and unreviewed executable instructions.
5. When adaptation is needed, preserve source attribution, do not invent an upstream license, keep secrets in environment variables, add bounded diagnostics/timeouts, and exercise list/describe/call paths against a harmless fixture when the real external service is unavailable.
6. Separate executor correctness from external-service readiness: a fixture can verify the adapter, while live readiness still requires the actual client, endpoint, and credentials.

Do not infer capability from branding. For example, “omni” may mean cross-client distribution rather than multimodal skills. A genuine multimodal skill workflow needs visual assets, explicit instructions for when they are evidence, and an on-demand image-reading path appropriate to the active agent.

See `references/hermes-skill-adaptation-review.md` for the condensed review checklist.

## Verification

Do not treat a directory or CLI list entry alone as success. An empty `SKILL.md` can still appear in `hermes skills list` as a local skill.

Verify all of these before finalizing:

```bash
wc -c ~/.hermes/skills/NAME/SKILL.md
hermes skills list | grep -i NAME
```

Then load it:

```python
skill_view(name="NAME")
```

A valid install has nonzero file size, frontmatter with `name:` and `description:` where available, and `skill_view` returns the expected content.

## Pitfalls

- Do not trust the native installer's exit code alone. Some fetch failures can still return status 0 while printing `Error:`; inspect output and require list/load/content verification.
- Multi-line shell snippets are easy for users to paste incorrectly. When handing commands to the user, prefer one-line commands for simple installs, or a clean heredoc block that starts and ends exactly.
- `hermes skills list` only proves Hermes sees a directory or file. It does not prove the skill content is intact.
- If a user has already cloned the repository, prefer copying from that local clone over repeating slow network fetches.
- When a GitHub repo has `SKILL.md` in the root, the install name usually comes from the frontmatter `name:` field. If parsing is inconvenient, use the repo name as a conservative directory name and verify with `skill_view`.
- Protected bundled skills such as `hermes-agent` should not be patched with one-off install fallbacks. Put operational workarounds in this umbrella instead.

## Related Reference

See `references/github-skill-install-fallbacks.md` for a condensed transcript-derived example covering an empty local skill file, local clone repair, and codeload zip fallback.