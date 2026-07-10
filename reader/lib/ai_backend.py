#!/usr/bin/env python3
"""
AI Backend abstraction layer.

Allows paper_daemon.py to work with multiple AI agent backends instead of
being hard-wired to the Claude Code CLI.

Supported backends:
  - claude_code : Claude Code CLI (original behavior, kept as default)
  - generic_cli : Any CLI tool that accepts a prompt via stdin or arg
  - openai_api  : OpenAI-compatible chat completion API

Backend selection is driven by ``_shared/user-config.json`` under the
``ai_backend`` key.  Users can also drop in a ``user-config.local.json``
override file without touching the tracked default.
"""

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

_SHARED_DIR = Path(__file__).resolve().parents[2] / "_shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from user_config import ai_backend_config, ai_backend_subconfig, ai_backend_type


# ── Exceptions ────────────────────────────────────────────────────────────────

class AIBackendError(Exception):
    """Base exception for AI backend failures."""


class RateLimitError(AIBackendError):
    """Backend hit a rate limit (transient, retry after waiting)."""

    def __init__(self, message: str = "", wait_seconds: Optional[int] = None):
        super().__init__(message)
        self.wait_seconds = wait_seconds


class QuotaLimitError(AIBackendError):
    """Backend hit a usage quota limit (wait until reset)."""

    def __init__(self, message: str = "", wait_seconds: Optional[int] = None):
        super().__init__(message)
        self.wait_seconds = wait_seconds


class BackendTimeoutError(AIBackendError):
    """Backend call timed out."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_reset_wait_seconds(message: str) -> Optional[int]:
    """Parse ``resets 9pm (Asia/Shanghai)`` style hints to compute wait seconds."""
    match = re.search(
        r"resets\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?(?:\s*\(([^)]+)\))?",
        message,
        re.IGNORECASE,
    )
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    ampm = (match.group(3) or "").lower()
    tz_name = match.group(4) or "Asia/Shanghai"

    if ampm == "pm" and hour < 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0

    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(tz_name)
    except Exception:
        return None

    now = datetime.now(tz)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target = target + timedelta(days=1)

    return max(60, int((target - now).total_seconds()))


# ── Backend presets ───────────────────────────────────────────────────────────

BACKEND_PRESETS: dict[str, dict] = {
    "claude": {
        "type": "claude_code",
        "claude_code": {
            "command": "claude",
            "model": "opus",
            "extra_args": [
                "--permission-mode", "acceptEdits",
                "--dangerously-skip-permissions",
            ],
        },
    },
    "codex": {
        "type": "generic_cli",
        "generic_cli": {
            "command": "codex",
            "args": ["exec", "--sandbox", "workspace-write"],
            "input_mode": "arg",
            "prompt_arg": "",
        },
    },
    "openai": {
        "type": "openai_api",
        "openai_api": {
            "model": "gpt-4o",
            "api_key_env": "OPENAI_API_KEY",
            "base_url": "https://api.openai.com/v1",
            "max_tokens": 16384,
            "temperature": 0.7,
        },
    },
}


# ── Abstract base ─────────────────────────────────────────────────────────────

class AIBackend(ABC):
    """Abstract base class for all AI backends."""

    @abstractmethod
    def process(self, prompt: str, timeout: int = 900) -> str:
        """Send *prompt* to the AI and return its textual output.

        Raises:
            RateLimitError:      transient rate limit, safe to retry after wait.
            QuotaLimitError:     usage quota exhausted, wait for reset.
            BackendTimeoutError: the call did not finish in time.
            AIBackendError:      any other unrecoverable failure.
        """

    @staticmethod
    def from_config(config: Optional[dict] = None, preset: Optional[str] = None) -> "AIBackend":
        """Factory: build a backend from a *preset*, explicit *config*, or the
        shared user config (in that priority order).

        Args:
            config:  Full backend config dict with a ``type`` key.
            preset:  Shortcut name — one of ``claude``, ``codex``, ``openai``.
        """
        if preset:
            if preset not in BACKEND_PRESETS:
                raise AIBackendError(
                    f"Unknown backend preset: {preset!r}. "
                    f"Available: {', '.join(BACKEND_PRESETS)}"
                )
            config = BACKEND_PRESETS[preset]

        if config is None:
            backend_type = ai_backend_type()
        else:
            backend_type = config.get("type", "claude_code")

        if backend_type == "claude_code":
            sub = config.get("claude_code", {}) if config else ai_backend_subconfig("claude_code")
            return ClaudeCodeBackend(sub)
        if backend_type == "generic_cli":
            sub = config.get("generic_cli", {}) if config else ai_backend_subconfig("generic_cli")
            return GenericCLIBackend(sub)
        if backend_type == "openai_api":
            sub = config.get("openai_api", {}) if config else ai_backend_subconfig("openai_api")
            return OpenAIAPIBackend(sub)

        raise AIBackendError(f"Unknown AI backend type: {backend_type!r}")

    @staticmethod
    def from_cli_args(
        preset: Optional[str] = None,
        cli_command: Optional[str] = None,
        cli_args: Optional[str] = None,
        cli_input_mode: Optional[str] = None,
        cli_prompt_arg: Optional[str] = None,
        api_model: Optional[str] = None,
        api_key_env: Optional[str] = None,
        api_base_url: Optional[str] = None,
    ) -> "AIBackend":
        """Build a backend from command-line arguments.

        Priority: CLI overrides > preset > user-config.json.

        Args:
            preset:         Preset name (``claude``, ``codex``, ``openai``).
            cli_command:    Override CLI command for generic_cli / claude_code.
            cli_args:       Comma-separated CLI args.
            cli_input_mode: ``stdin`` or ``arg``.
            cli_prompt_arg: Argument name for the prompt (empty = positional).
            api_model:      Model name for openai_api or claude_code.
            api_key_env:    Environment variable name for API key.
            api_base_url:   API base URL.
        """
        import copy

        # Start from preset or user config
        if preset:
            config = copy.deepcopy(BACKEND_PRESETS[preset])
        else:
            config = None  # fall back to from_config() reading user-config.json

        # If no preset and no overrides, just use user config
        if config is None and not any([
            cli_command, cli_args, cli_input_mode is not None,
            cli_prompt_arg is not None, api_model, api_key_env, api_base_url,
        ]):
            return AIBackend.from_config()

        # If we have overrides but no preset, build a custom config
        if config is None:
            # Guess the backend type from which overrides were given
            if api_model or api_key_env or api_base_url:
                config = {"type": "openai_api", "openai_api": {}}
            else:
                config = {"type": "generic_cli", "generic_cli": {}}

        backend_type = config["type"]

        # Apply CLI overrides
        if backend_type == "claude_code":
            sub = config.setdefault("claude_code", {})
            if cli_command:
                sub["command"] = cli_command
            if api_model:
                sub["model"] = api_model
            if cli_args:
                sub["extra_args"] = cli_args.split(",")
        elif backend_type == "generic_cli":
            sub = config.setdefault("generic_cli", {})
            if cli_command:
                sub["command"] = cli_command
            if cli_args:
                sub["args"] = cli_args.split(",")
            if cli_input_mode:
                sub["input_mode"] = cli_input_mode
            if cli_prompt_arg is not None:
                sub["prompt_arg"] = cli_prompt_arg
        elif backend_type == "openai_api":
            sub = config.setdefault("openai_api", {})
            if api_model:
                sub["model"] = api_model
            if api_key_env:
                sub["api_key_env"] = api_key_env
            if api_base_url:
                sub["base_url"] = api_base_url

        return AIBackend.from_config(config)


# ── Claude Code CLI backend ───────────────────────────────────────────────────

class ClaudeCodeBackend(AIBackend):
    """Claude Code CLI backend — preserves the original daemon behavior."""

    def __init__(self, config: dict):
        self.command: str = config.get("command", "claude")
        self.model: str = config.get("model", "opus")
        self.extra_args: list[str] = config.get("extra_args", [
            "--permission-mode", "acceptEdits",
            "--dangerously-skip-permissions",
        ])

    def process(self, prompt: str, timeout: int = 900) -> str:
        cmd = [self.command, "-p", prompt, "--model", self.model] + list(self.extra_args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            raise BackendTimeoutError("Claude Code call timed out")

        output = result.stdout + result.stderr
        self._check_limit_errors(output)

        if result.returncode != 0:
            raise AIBackendError(
                f"Claude Code failed (exit {result.returncode}): {output[:500]}"
            )
        return output

    @staticmethod
    def _check_limit_errors(output: str) -> None:
        text = output.lower()
        if "rate limit" in text or "too many requests" in text:
            raise RateLimitError(output[:200])
        if "hit your limit" in text or "usage limit" in text or "resets" in text:
            wait = parse_reset_wait_seconds(output)
            raise QuotaLimitError(output[:200], wait_seconds=wait)


# ── Generic CLI backend ───────────────────────────────────────────────────────

class GenericCLIBackend(AIBackend):
    """Works with any CLI tool that accepts a prompt.

    The prompt can be fed via **stdin** (``input_mode: "stdin"``) or as a
    command-line argument (``input_mode: "arg"``).
    """

    def __init__(self, config: dict):
        self.command: str = config.get("command", "")
        if not self.command:
            raise AIBackendError("generic_cli backend requires a non-empty 'command'")
        self.args: list[str] = config.get("args", [])
        self.input_mode: str = config.get("input_mode", "stdin")
        self.prompt_arg: str = config.get("prompt_arg", "-p")

    def process(self, prompt: str, timeout: int = 900) -> str:
        if self.input_mode == "stdin":
            cmd = [self.command] + list(self.args)
            try:
                result = subprocess.run(
                    cmd,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                raise BackendTimeoutError("CLI call timed out")
        else:
            # When prompt_arg is empty, the prompt is passed as a bare
            # positional argument (e.g.  codex exec "prompt").
            if self.prompt_arg:
                cmd = [self.command] + list(self.args) + [self.prompt_arg, prompt]
            else:
                cmd = [self.command] + list(self.args) + [prompt]
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                raise BackendTimeoutError("CLI call timed out")

        output = result.stdout + result.stderr
        self._check_generic_errors(output)

        if result.returncode != 0:
            raise AIBackendError(
                f"CLI failed (exit {result.returncode}): {output[:500]}"
            )
        return output

    @staticmethod
    def _check_generic_errors(output: str) -> None:
        text = output.lower()
        if "rate limit" in text or "too many requests" in text or "429" in text:
            raise RateLimitError(output[:200])
        if "quota" in text and "exceeded" in text:
            raise QuotaLimitError(output[:200])


# ── OpenAI-compatible API backend ─────────────────────────────────────────────

class OpenAIAPIBackend(AIBackend):
    """OpenAI-compatible chat-completion API backend.

    Works with the official OpenAI API as well as any OpenAI-compatible
    endpoint (Azure OpenAI, vLLM, Ollama, LM Studio, etc.) — just set a
    different ``base_url`` in the config.
    """

    def __init__(self, config: dict):
        self.model: str = config.get("model", "gpt-4o")
        api_key_env = config.get("api_key_env", "OPENAI_API_KEY")
        self.api_key: str = os.environ.get(api_key_env, "")
        if not self.api_key:
            raise AIBackendError(
                f"API key not found in environment variable: {api_key_env}"
            )
        self.base_url: str = config.get("base_url", "https://api.openai.com/v1")
        self.max_tokens: int = config.get("max_tokens", 16384)
        self.temperature: float = config.get("temperature", 0.7)

    def process(self, prompt: str, timeout: int = 900) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as err:
            body = ""
            try:
                body = err.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            if err.code == 429:
                retry_after = err.headers.get("Retry-After")
                wait = int(retry_after) if retry_after and retry_after.isdigit() else None
                raise RateLimitError(f"HTTP 429: {body[:200]}", wait_seconds=wait)
            if err.code == 402:
                raise QuotaLimitError(f"HTTP 402: {body[:200]}")
            raise AIBackendError(f"API error (HTTP {err.code}): {body[:500]}")
        except urllib.error.URLError as err:
            if "timed out" in str(err).lower():
                raise BackendTimeoutError(f"API call timed out: {err}")
            raise AIBackendError(f"Network error: {err}")
