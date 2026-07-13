# Source and adaptation notes

Adapted from: <https://github.com/OrayDev/awesun-skill>

Upstream files were retrieved from the `main` branch on 2026-07-13. The upstream repository did not advertise a license through the GitHub API at retrieval time; preserve this attribution and consult the upstream repository before redistribution.

Hermes adaptation changes:

- installs under `~/.hermes/skills/productivity/awesun-remote-control`;
- replaces Claude-specific paths with Hermes paths;
- fixes `MCPExecutor.connect()` referencing undefined `server_config` instead of `self.server_config`;
- merges the inherited process environment instead of replacing it;
- keeps `AWESUN_API_TOKEN` outside the checked-in config;
- resolves Windows paths under WSL and checks common AweSun locations;
- adds `--check`, timeouts, input validation, secret masking, and clearer errors;
- returns live MCP schemas from `--list` and `--describe`.
