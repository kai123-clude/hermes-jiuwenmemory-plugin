---
name: hermes-skill-operations
description: Install, repair, and verify Hermes skills from hub identifiers, GitHub repositories, or local SKILL.md files, including fallback fetch paths and empty-skill detection.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, skills, installation, troubleshooting, github]
---

# Hermes Skill Operations

Use this skill when installing, repairing, updating, or verifying Hermes skills in the active profile's skill library, especially when the user gives a hub identifier such as `owner/repo`, a GitHub repository, or a direct `SKILL.md` URL.

## Workflow

1. Prefer the official installer first:

   ```bash
   hermes skills install <identifier> --force --yes
   ```

   Use `--yes` in TUI contexts to avoid an interactive confirmation prompt. Use `--force` only when the user requested it or when the task is explicitly to install despite scanner warnings.

2. If the installer cannot resolve `owner/repo`, inspect the repository layout for a root `SKILL.md` before assuming the identifier is invalid:

   ```bash
   curl -fsSL 'https://api.github.com/repos/<owner>/<repo>/contents/?ref=main'
   ```

   Look for a `SKILL.md` entry and its `download_url`.

3. Try direct URL installation when a `download_url` exists:

   ```bash
   hermes skills install 'https://raw.githubusercontent.com/<owner>/<repo>/main/SKILL.md' --force --yes
   ```

4. If direct raw fetching is unavailable in the current environment, fetch through the GitHub contents API and decode the base64 payload into the active profile skill directory:

   ```bash
   mkdir -p ~/.hermes/skills/<skill-name> && curl -fsSL 'https://api.github.com/repos/<owner>/<repo>/contents/SKILL.md?ref=main' | python3 -c 'import sys,json,base64; print(base64.b64decode(json.load(sys.stdin)["content"]).decode("utf-8"))' > ~/.hermes/skills/<skill-name>/SKILL.md
   ```

   Keep this as a single shell line when handing it to the user; broken newlines around the URL, pipe, or Python string can create an empty `SKILL.md`.

5. Verify the installed skill is real, not just a directory placeholder:

   ```bash
   wc -c ~/.hermes/skills/<skill-name>/SKILL.md
   hermes skills list | grep -i '<skill-name>'
   ```

   A skill can appear in `hermes skills list` even when `SKILL.md` is zero bytes. Always check file size or load it with `skill_view` before declaring success.

6. In the current agent session, use `skill_view(name='<skill-name>')` when available to confirm that frontmatter, description, and content load correctly.

## Pitfalls

- `hermes skills list` proves a skill directory is discoverable, not that the skill content is complete.
- Shell line wrapping can split `curl`, the quoted URL, the pipe, or the Python command. For user-facing recovery commands, provide a copy-pasteable single line.
- Do not turn a transient fetch failure into a durable claim that a domain or installer is broken. Capture and use the fallback fetch path instead.
- Profile scope matters: write skills under the active profile's `$HERMES_HOME/skills/`; for the default profile this is usually `~/.hermes/skills/`.

## Reference

See `references/github-skill-install-fallbacks.md` for a concrete fallback recipe and verification checklist.