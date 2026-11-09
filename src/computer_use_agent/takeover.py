"""Human-takeover detection and handoff files."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

CAPTCHA_MARKERS = ("captcha", "verify you are human", "i'm not a robot", "recaptcha")
LOGIN_MARKERS = ("sign in to continue", "login required", "password", "two-factor", "2fa code")


@dataclass
class TakeoverEvent:
    """A recorded takeover handoff."""

    reason: str
    url: str
    page_preview: str = ""
    timestamp: float = field(default_factory=time.time)


class TakeoverDetector:
    """Detect states a bot should not push through alone."""

    def inspect(self, html: str, url: str = "") -> TakeoverEvent | None:
        """Return a TakeoverEvent if the page needs a human, else None."""
        low = html.lower()
        if any(m in low for m in CAPTCHA_MARKERS):
            return TakeoverEvent("captcha", url, html[:200])
        if 'type="password"' in low or any(m in low for m in LOGIN_MARKERS[:2]):
            return TakeoverEvent("login_wall", url, html[:200])
        if "two-factor" in low or "2fa code" in low:
            return TakeoverEvent("two_factor", url, html[:200])
        if not html.strip():
            return TakeoverEvent("unknown_state", url, "")
        return None

    @staticmethod
    def write_handoff(event: TakeoverEvent, path: Path) -> Path:
        """Write a handoff JSON file for a human operator."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(event), indent=2), encoding="utf-8")
        return path
