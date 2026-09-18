"""Platform constraints validator and auto-trimmer for social delivery networks."""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ValidationResult(BaseModel):
    """Result of platform format and constraint validation."""
    model_config = ConfigDict(extra="ignore")

    valid: bool
    platform: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    auto_trimmed_text: str | None = None
    char_count: int
    max_chars: int


class SocialValidator:
    """Validator for social media platform constraints, character caps, and media formats."""

    PLATFORM_CONSTRAINTS: dict[str, dict[str, Any]] = {
        "tiktok": {
            "max_chars": 2200,
            "max_hashtags": 10,
            "required_aspect_ratio": "9:16",
            "max_video_duration": 600.0,
        },
        "instagram": {
            "max_chars": 2200,
            "max_hashtags": 30,
            "allowed_aspect_ratios": ["9:16", "1:1", "4:5"],
            "max_video_duration": 90.0,
        },
        "threads": {
            "max_chars": 500,
            "max_hashtags": 10,
        },
        "facebook": {
            "max_chars": 63206,
            "allowed_aspect_ratios": ["16:9", "1:1"],
        },
        "x": {
            "max_chars": 280,
            "max_hashtags": 4,
            "max_video_duration": 140.0,
        },
        "youtube": {
            "max_chars_title": 100,
            "max_chars_desc": 5000,
            "required_aspect_ratio": "9:16",
            "max_video_duration": 60.0,
            "requires_shorts_tag": True,
        },
    }

    @classmethod
    def auto_trim(cls, platform: str, text: str) -> str:
        """Trims text cleanly at the last sentence/word boundary to fit platform max_chars without cutting words in half."""
        plat = platform.strip().lower()
        if plat not in cls.PLATFORM_CONSTRAINTS:
            raise ValueError(f"Unsupported platform '{platform}'. Supported: {list(cls.PLATFORM_CONSTRAINTS.keys())}")

        constraints = cls.PLATFORM_CONSTRAINTS[plat]
        max_chars = constraints.get("max_chars") or constraints.get("max_chars_desc", 5000)

        if len(text) <= max_chars:
            return text

        truncated = text[:max_chars]

        # If next character in original text is whitespace, cleanly strip trailing spaces
        if text[max_chars].isspace():
            return truncated.rstrip()

        # Try to find a clean sentence boundary (.!? followed by whitespace or end)
        # Only accept sentence boundaries that preserve a meaningful portion (>= 40% of max_chars)
        min_sentence_len = max(20, int(max_chars * 0.4))
        sentence_matches = [m.end() for m in re.finditer(r"[.!?](\s+|$)", truncated)]
        valid_sentence_matches = [pos for pos in sentence_matches if pos >= min_sentence_len]
        if valid_sentence_matches:
            best_sentence_end = valid_sentence_matches[-1]
            return truncated[:best_sentence_end].strip()

        # Fallback to last clean word boundary (whitespace)
        last_space = max(truncated.rfind(" "), truncated.rfind("\n"), truncated.rfind("\t"))
        if last_space > 0:
            return truncated[:last_space].rstrip()

        # If no whitespace boundary exists at all (e.g. continuous non-space string)
        return truncated

    @classmethod
    def validate_post(
        cls,
        platform: str,
        text: str,
        media_aspect_ratio: str | None = None,
        media_duration_seconds: float | None = None,
    ) -> ValidationResult:
        """Validates character limits, hashtag limits, video aspect ratio, and duration limits."""
        plat = platform.strip().lower()
        char_count = len(text)

        if plat not in cls.PLATFORM_CONSTRAINTS:
            return ValidationResult(
                valid=False,
                platform=platform,
                errors=[f"Unsupported platform '{platform}'. Supported: {list(cls.PLATFORM_CONSTRAINTS.keys())}"],
                warnings=[],
                auto_trimmed_text=None,
                char_count=char_count,
                max_chars=0,
            )

        constraints = cls.PLATFORM_CONSTRAINTS[plat]
        max_chars = constraints.get("max_chars") or constraints.get("max_chars_desc", 5000)

        errors: list[str] = []
        warnings: list[str] = []
        auto_trimmed_text: str | None = None

        # 1. Validate Character Limit
        if char_count > max_chars:
            errors.append(
                f"{plat.capitalize()} text length ({char_count}) exceeds maximum allowed of {max_chars} characters."
            )
            auto_trimmed_text = cls.auto_trim(plat, text)
            if plat == "threads":
                warnings.append("Threads post exceeds 500 chars. Consider splitting into a multi-post thread.")

        # 2. Validate YouTube Title/Description specific limits
        if plat == "youtube":
            max_title = constraints.get("max_chars_title", 100)
            if "\n" in text:
                first_line = text.split("\n", 1)[0].strip()
                if len(first_line) > max_title:
                    errors.append(
                        f"YouTube Shorts title ({len(first_line)} chars) exceeds maximum allowed of {max_title} characters."
                    )

        # 3. Validate Hashtag Limits
        hashtags = re.findall(r"#\w+", text)
        max_hashtags = constraints.get("max_hashtags")
        if max_hashtags is not None and len(hashtags) > max_hashtags:
            errors.append(
                f"{plat.capitalize()} allows at most {max_hashtags} hashtags (found {len(hashtags)})."
            )

        # 4. Validate YouTube Shorts Required Tag
        if constraints.get("requires_shorts_tag"):
            if not re.search(r"#shorts\b", text, re.IGNORECASE):
                errors.append("YouTube Shorts requires '#Shorts' tag in the text or title.")

        # 5. Validate Aspect Ratio
        if media_aspect_ratio is not None:
            aspect = media_aspect_ratio.strip().lower()
            req_ratio = constraints.get("required_aspect_ratio")
            if req_ratio is not None and aspect != req_ratio.lower():
                errors.append(
                    f"{plat.capitalize()} requires aspect ratio '{req_ratio}', got '{media_aspect_ratio}'."
                )

            allowed_ratios = constraints.get("allowed_aspect_ratios")
            if allowed_ratios is not None:
                allowed_lower = [r.lower() for r in allowed_ratios]
                if aspect not in allowed_lower:
                    errors.append(
                        f"{plat.capitalize()} only allows aspect ratios {allowed_ratios}, got '{media_aspect_ratio}'."
                    )
        else:
            # Add advisory warning if vertical format is recommended/required for best performance
            if constraints.get("required_aspect_ratio") == "9:16":
                warnings.append(
                    f"{plat.capitalize()} operates best with vertical 9:16 video media."
                )

        # 6. Validate Video Duration
        if media_duration_seconds is not None:
            max_duration = constraints.get("max_video_duration")
            if max_duration is not None and media_duration_seconds > max_duration:
                errors.append(
                    f"{plat.capitalize()} video duration ({media_duration_seconds:.1f}s) exceeds maximum allowed duration of {max_duration:.1f}s."
                )
            elif media_duration_seconds <= 0:
                errors.append(f"Media duration must be greater than 0s, got {media_duration_seconds:.1f}s.")

        valid = len(errors) == 0

        return ValidationResult(
            valid=valid,
            platform=plat,
            errors=errors,
            warnings=warnings,
            auto_trimmed_text=auto_trimmed_text,
            char_count=char_count,
            max_chars=max_chars,
        )
