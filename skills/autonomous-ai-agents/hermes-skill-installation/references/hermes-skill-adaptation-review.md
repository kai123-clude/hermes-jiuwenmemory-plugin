# Hermes Skill Adaptation Review

Use this checklist when a repository claims to contain a skill but is not already a verified Hermes-native package.

## Classify the Repository

- **Single skill:** one root or nested `SKILL.md` plus local support files.
- **Multi-skill repository:** many independently installable directories.
- **Catalog/distributor:** manifests, CLI, bundles, API, MCP, or A2A around many skills; do not treat the repository itself as one skill.
- **Meta-skill:** generates or transforms other skills; verify both generation and consumption paths.

## Inspect Before Installing

- Find all `SKILL.md` files and read frontmatter.
- Read every executable helper and configuration file in the selected skill.
- Identify hard-coded client paths, OS-specific commands, placeholder credentials, and missing dependencies.
- Check upstream license metadata; use an explicit “upstream unspecified” marker rather than inventing a license.
- Preserve attribution when adapting content or code.

## Adapt for Hermes

- Install only the selected skill under an appropriate class-level category.
- Replace client-specific paths and invocation instructions with Hermes paths/tools.
- Keep tokens and API keys in environment variables, not tracked config or chat.
- Merge inherited process environment when spawning MCP servers.
- Add `--check` diagnostics, bounded timeouts, argument validation, and secret masking to executors.
- Add safety gates for disruptive remote actions.

## Verify in Layers

1. Syntax/frontmatter validation.
2. Hermes discovery through `hermes skills list`.
3. Exact load through `skill_view`.
4. Executor protocol test using a harmless local fixture when feasible.
5. Live readiness check against the actual external client/service.
6. One read-only live call before state-changing operations.

Do not report a live integration as ready merely because the fixture passed. Report adapter correctness and external readiness separately.

## Multimodal Claim Test

A repository name containing “omni” is not evidence of multimodality. For a genuine multimodal skill workflow, look for all three layers:

1. **Creation:** extraction of useful screenshots, images, audio, or video keyframes from source material.
2. **Artifact:** visual assets packaged with text and explicitly tied to steps or quality criteria.
3. **Consumption:** runtime capability detection and on-demand image loading rather than injecting all assets at startup.

For Hermes, text can be loaded with `skill_view`/`read_file`, but image pixels require a vision-capable tool such as `vision_analyze`. Make that handoff explicit in the skill.

## Bulk Catalog Warning

Prefer search-and-select over full import. Large catalogs commonly contain duplicate names, version variants, overlapping triggers, warnings, and client-specific assumptions. Review and adapt one chosen skill at a time unless the user explicitly requests a vetted bundle.
