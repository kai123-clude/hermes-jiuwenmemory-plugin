#!/usr/bin/env python3
"""Hermes-compatible AweSun MCP skill executor."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
import urllib.request
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    HAS_MCP = True
except ImportError:
    HAS_MCP = False

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SKILL_DIR / "mcp-config.json"
PLACEHOLDERS = {"", "your-mcp-server-token", "xxxxxxxx", "xxxxxxxxxxx"}


def windows_to_wsl(value: str) -> str:
    """Translate C:\\path to /mnt/c/path when running under WSL."""
    if len(value) >= 3 and value[1:3] in {":\\", ":/"} and Path("/proc/sys/fs/binfmt_misc/WSLInterop").exists():
        drive = value[0].lower()
        return f"/mnt/{drive}/{value[3:].replace(chr(92), '/')}"
    return value


def candidate_commands() -> list[str]:
    candidates = [
        r"C:\Program Files\Oray\Awesun\awesun-mcp-server.exe",
        r"C:\Program Files\Oray\Awesun\awesun-mcp-server",
        r"C:\Program Files (x86)\Oray\Awesun\awesun-mcp-server.exe",
        r"C:\Program Files (x86)\Oray\Awesun\awesun-mcp-server",
        "/Applications/AweSun.app/Contents/Helpers/awesun-mcp-server",
    ]
    return [windows_to_wsl(item) for item in candidates]


def load_raw_config() -> dict[str, Any]:
    path = Path(os.environ.get("AWESUN_MCP_CONFIG", str(DEFAULT_CONFIG))).expanduser()
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if "mcpServers" in data:
        return data.get("mcpServers", {}).get("awesun-mcp-server", {})
    return data


def resolve_command(config: dict[str, Any]) -> str:
    configured = os.environ.get("AWESUN_MCP_COMMAND") or str(config.get("command", ""))
    if configured:
        translated = windows_to_wsl(os.path.expandvars(os.path.expanduser(configured)))
        if Path(translated).exists() or shutil.which(translated):
            return translated
        return translated
    for candidate in candidate_commands():
        if Path(candidate).exists():
            return candidate
    return ""


def build_server_config() -> dict[str, Any]:
    raw = load_raw_config()
    command = resolve_command(raw)
    env = os.environ.copy()
    for key, value in raw.get("env", {}).items():
        expanded = os.path.expandvars(str(value))
        if expanded not in PLACEHOLDERS and not (expanded.startswith("${") and expanded.endswith("}")):
            env[str(key)] = expanded
    env["AWESUN_API_URL"] = os.environ.get(
        "AWESUN_API_URL", env.get("AWESUN_API_URL", "http://127.0.0.1:8908")
    )
    token = os.environ.get("AWESUN_API_TOKEN", env.get("AWESUN_API_TOKEN", ""))
    if token in PLACEHOLDERS:
        token = ""
    if token:
        env["AWESUN_API_TOKEN"] = token
    else:
        env.pop("AWESUN_API_TOKEN", None)
    return {"command": command, "args": list(raw.get("args", [])), "env": env}


def check_setup() -> dict[str, Any]:
    config = build_server_config()
    command = config["command"]
    command_found = bool(command) and (Path(command).exists() or shutil.which(command) is not None)
    token_set = bool(config["env"].get("AWESUN_API_TOKEN"))
    url = config["env"].get("AWESUN_API_URL", "http://127.0.0.1:8908")
    api_reachable = False
    api_error = ""
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            api_reachable = response.status < 500
    except Exception as exc:  # endpoint may return non-2xx; report rather than leak details
        api_error = str(exc)
    return {
        "ready": bool(HAS_MCP and command_found and token_set and api_reachable),
        "mcp_python_package": HAS_MCP,
        "command": command or None,
        "command_found": command_found,
        "api_url": url,
        "api_reachable": api_reachable,
        "api_error": api_error or None,
        "token_set": token_set,
        "token_value": "***" if token_set else None,
    }


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "__dict__"):
        return {key: to_jsonable(item) for key, item in vars(value).items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    return value


class MCPExecutor:
    def __init__(self, server_config: dict[str, Any], timeout: float = 20):
        if not HAS_MCP:
            raise RuntimeError("Python package 'mcp' is not installed")
        if not server_config.get("command"):
            raise RuntimeError("AweSun MCP command not found; set AWESUN_MCP_COMMAND")
        if not server_config.get("env", {}).get("AWESUN_API_TOKEN"):
            raise RuntimeError("AWESUN_API_TOKEN is not set")
        self.server_config = server_config
        self.timeout = timeout
        self.session: ClientSession | None = None
        self.exit_stack: AsyncExitStack | None = None

    async def connect(self) -> None:
        params = StdioServerParameters(
            command=self.server_config["command"],
            args=self.server_config.get("args", []),
            env=self.server_config["env"],
        )
        self.exit_stack = AsyncExitStack()
        transport = await asyncio.wait_for(
            self.exit_stack.enter_async_context(stdio_client(params)), self.timeout
        )
        read_stream, write_stream = transport
        self.session = await asyncio.wait_for(
            self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream)), self.timeout
        )
        await asyncio.wait_for(self.session.initialize(), self.timeout)

    async def ensure_connected(self) -> ClientSession:
        if not self.session:
            await self.connect()
        assert self.session is not None
        return self.session

    async def list_tools(self) -> list[dict[str, Any]]:
        session = await self.ensure_connected()
        response = await asyncio.wait_for(session.list_tools(), self.timeout)
        return [
            {"name": tool.name, "description": tool.description, "inputSchema": tool.inputSchema}
            for tool in response.tools
        ]

    async def describe_tool(self, name: str) -> dict[str, Any] | None:
        for tool in await self.list_tools():
            if tool["name"] == name:
                return tool
        return None

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        session = await self.ensure_connected()
        return await asyncio.wait_for(session.call_tool(name, arguments), self.timeout)

    async def close(self) -> None:
        if self.exit_stack:
            try:
                await self.exit_stack.aclose()
            except (Exception, asyncio.CancelledError):
                pass


async def run(args: argparse.Namespace) -> int:
    if args.check:
        status = check_setup()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 0 if status["ready"] else 2

    executor = MCPExecutor(build_server_config(), timeout=args.timeout)
    try:
        if args.list:
            result = await executor.list_tools()
        elif args.describe:
            result = await executor.describe_tool(args.describe)
            if result is None:
                raise RuntimeError(f"Tool not found: {args.describe}")
        elif args.call:
            payload = json.loads(args.call)
            if not isinstance(payload, dict) or not isinstance(payload.get("tool"), str):
                raise ValueError("--call JSON requires a string 'tool' field")
            arguments = payload.get("arguments", {})
            if not isinstance(arguments, dict):
                raise ValueError("--call 'arguments' must be an object")
            result = await executor.call_tool(payload["tool"], arguments)
        else:
            raise RuntimeError("Choose --check, --list, --describe, or --call")
        print(json.dumps(to_jsonable(result), indent=2, ensure_ascii=False))
        return 0
    finally:
        await executor.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="AweSun MCP skill executor for Hermes")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Check local prerequisites")
    group.add_argument("--list", action="store_true", help="List MCP tools and schemas")
    group.add_argument("--describe", metavar="TOOL", help="Describe one MCP tool")
    group.add_argument("--call", metavar="JSON", help="Call a tool with a JSON object")
    parser.add_argument("--timeout", type=float, default=20, help="Timeout in seconds")
    parser.add_argument("--debug", action="store_true", help="Show traceback on errors")
    args = parser.parse_args()
    try:
        return asyncio.run(run(args))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if args.debug:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
