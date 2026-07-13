# Porting and verification notes

Use this checklist when importing or refreshing a multimodal Skill from an official application bundle.

## Provenance

1. Start from the publisher's release API/page, not a similarly named third-party repository.
2. Record the exact release URL, release date/version, and a locally computed SHA-256.
3. Check both the public Skill catalog and the official application bundle. A bundled Skill may not be listed separately in the catalog.
4. Preserve the upstream `SKILL.md` as a reference, but make the Hermes-facing `SKILL.md` an adapter rather than silently rewriting provenance.
5. If the individual Skill has no explicit license, keep it local and do not claim redistribution rights.

## Safe extraction

- Prefer archive extraction over installation.
- If the installer format is newer than available extractors, use an isolated temporary install only after user approval.
- Silent installers can still launch the application. After extraction, check for spawned processes, terminate only the processes started by the temporary install, run the uninstaller when available, and remove the temporary directory.
- Do not leave the downloaded installer or transient work products unless the user asks to keep them.

## Hermes adaptation checklist

- Map client-specific tool names to actual Hermes tools.
- Use `vision_analyze` for image pixels; `read_file` is for text and structured files.
- Keep dynamic-page acquisition as a browser-tool fallback instead of requiring a second bundled browser runtime.
- Use a Skill-local virtual environment and a pinned dependency file.
- Make heavyweight browser automation optional when a static `requests`/BeautifulSoup path plus Hermes browser fallback is sufficient.
- Remove implicit browser-cookie access. Authenticated content requires explicit user approval and an explicit credential-safe path.
- Validate public HTTP(S) destinations and reject localhost, private/link-local/metadata addresses, embedded credentials, unsafe redirects, and path traversal.
- Require an explicit destination category when generating a new Hermes Skill.

## Focused ad-hoc verification

When no canonical test suite exists, create a temporary script under `/tmp` with a `hermes-verify-` prefix and run it with the Skill-local interpreter. Verify at least:

1. all shipped Python scripts compile;
2. safe slugs pass and traversal slugs fail;
3. public URLs pass while private/file/credential-bearing URLs fail;
4. the static HTML fallback returns ordered blocks without fabricating media;
5. output path traversal is blocked;
6. required baseline dependencies import;
7. Playwright absence is accepted when it is documented as optional.

Delete the temporary verification script and generated caches afterward. Report this as **ad-hoc verification**, not as a canonical suite being green.
