"""Unit tests for platform constraints validator and auto-trimmer."""
from __future__ import annotations

import pytest
from backend.services.social_validator import SocialValidator, ValidationResult


class TestSocialValidator:
    """Test suite for SocialValidator platform constraints and trimming."""

    def test_x_text_over_280_chars_fails_and_provides_auto_trimmed_text(self):
        """Test X text > 280 chars fails validation and provides auto_trimmed_text <= 280 chars."""
        long_sentence = (
            "Hari ini kami membakar donut gebu istimewa dengan uli 48 jam dan mentega asli. "
            "Setiap gigitan memberikan kepuasan maksimum yang tiada tandingan di mana-mana bakeri. "
            "Datanglah beramai-ramai ke kedai kami sebelum kehabisan stok kerana jualan kami hari ini sangat laris "
            "dan orang ramai sudah mula beratur panjang di hadapan kedai sejak jam 8 pagi tadi."
        )
        assert len(long_sentence) > 280

        result = SocialValidator.validate_post("x", long_sentence)

        assert not result.valid
        assert result.platform == "x"
        assert result.char_count == len(long_sentence)
        assert result.max_chars == 280
        assert any("280" in err for err in result.errors)
        assert result.auto_trimmed_text is not None
        assert len(result.auto_trimmed_text) <= 280

        # Ensure auto-trimmed text ends at a word/sentence boundary, not mid-word
        last_word = result.auto_trimmed_text.split()[-1]
        assert len(last_word) > 1

        # Re-validating the auto-trimmed text on X should not trigger character limit error
        trimmed_res = SocialValidator.validate_post("x", result.auto_trimmed_text)
        assert not any("exceeds maximum allowed of 280" in e for e in trimmed_res.errors)

    def test_threads_text_over_500_chars_fails_validation(self):
        """Test Threads text > 500 chars fails validation."""
        paragraph = (
            "Khairul Aming style recipe breakdown: Pertama sekali kita uli doh selama 48 jam "
            "menggunakan tepung gandum berprotein tinggi dan mentega tulen dari New Zealand. "
            "Selepas rehatkan doh pada suhu bilik, kita canai nipis dan terap bentuk donut bulat comel. "
            "Goreng dalam minyak panas berapi sederhana sehingga bertukar warna kuning keemasan yang rangup berderap. "
            "Angkat dan toskan, kemudian salut dengan karamel pekat meleleh yang panas berasap. "
            "Korang yang tengok video ni jangan sampai telan liur sorang-sorang! "
            "Komen kat bawah korang team coklat pekat atau team karamel leleh? Tag kawan korang yang suka donut!"
        )
        assert len(paragraph) > 500

        result = SocialValidator.validate_post("threads", paragraph)

        assert not result.valid
        assert result.platform == "threads"
        assert result.char_count == len(paragraph)
        assert result.max_chars == 500
        assert any("500" in err for err in result.errors)
        assert len(result.warnings) > 0
        assert any("thread" in w.lower() for w in result.warnings)
        assert result.auto_trimmed_text is not None
        assert len(result.auto_trimmed_text) <= 500

    def test_tiktok_requires_9_16_aspect_ratio_and_rejects_horizontal(self):
        """Test TikTok requires 9:16 aspect ratio (rejects 16:9 or horizontal)."""
        caption = "Donut gebu leleh viral TikTok! #dohnut #sedap"

        # Rejects 16:9
        res_16_9 = SocialValidator.validate_post("tiktok", caption, media_aspect_ratio="16:9")
        assert not res_16_9.valid
        assert any("9:16" in err for err in res_16_9.errors)

        # Rejects horizontal
        res_horizontal = SocialValidator.validate_post("tiktok", caption, media_aspect_ratio="horizontal")
        assert not res_horizontal.valid
        assert any("9:16" in err for err in res_horizontal.errors)

        # Rejects 4:3
        res_4_3 = SocialValidator.validate_post("tiktok", caption, media_aspect_ratio="4:3")
        assert not res_4_3.valid
        assert any("9:16" in err for err in res_4_3.errors)

        # Accepts 9:16
        res_valid = SocialValidator.validate_post("tiktok", caption, media_aspect_ratio="9:16", media_duration_seconds=45.0)
        assert res_valid.valid
        assert len(res_valid.errors) == 0

    def test_youtube_shorts_requires_duration_and_shorts_tag(self):
        """Test YouTube Shorts requires duration <= 60.0s and '#Shorts' tag."""
        # 1. Missing '#Shorts' tag fails
        res_no_tag = SocialValidator.validate_post(
            "youtube",
            "Resepi Donut Gebu Viral Hari Ini",
            media_aspect_ratio="9:16",
            media_duration_seconds=30.0,
        )
        assert not res_no_tag.valid
        assert any("shorts" in err.lower() for err in res_no_tag.errors)

        # 2. Duration > 60.0s fails
        res_long_duration = SocialValidator.validate_post(
            "youtube",
            "Resepi Donut Gebu #Shorts",
            media_aspect_ratio="9:16",
            media_duration_seconds=61.5,
        )
        assert not res_long_duration.valid
        assert any("duration" in err.lower() or "60" in err for err in res_long_duration.errors)

        # 3. Valid duration <= 60.0s and '#Shorts' tag passes
        res_valid = SocialValidator.validate_post(
            "youtube",
            "Resepi Donut Gebu #Shorts",
            media_aspect_ratio="9:16",
            media_duration_seconds=45.0,
        )
        assert res_valid.valid
        assert len(res_valid.errors) == 0

        # 4. Case-insensitive '#shorts' or '#SHORTS' is accepted
        res_lower_tag = SocialValidator.validate_post(
            "youtube",
            "Resepi Donut Gebu #shorts",
            media_aspect_ratio="9:16",
            media_duration_seconds=20.0,
        )
        assert res_lower_tag.valid
        assert len(res_lower_tag.errors) == 0

    def test_instagram_hashtag_limit_over_30_generates_error(self):
        """Test Instagram hashtag limit > 30 generates error."""
        too_many_hashtags = " ".join([f"#donut{i}" for i in range(35)])
        text_with_excess_tags = f"Fresh donuts daily! {too_many_hashtags}"

        res_excess = SocialValidator.validate_post("instagram", text_with_excess_tags)
        assert not res_excess.valid
        assert any("30" in err or "hashtag" in err.lower() for err in res_excess.errors)

        # Up to 30 hashtags is valid
        valid_hashtags = " ".join([f"#tag{i}" for i in range(30)])
        text_valid_tags = f"Fresh donuts daily! {valid_hashtags}"
        res_ok = SocialValidator.validate_post(
            "instagram",
            text_valid_tags,
            media_aspect_ratio="9:16",
            media_duration_seconds=30.0,
        )
        assert res_ok.valid
        assert len(res_ok.errors) == 0

    def test_valid_posts_pass_for_all_platforms(self):
        """Test valid posts pass for all platforms."""
        test_matrix = {
            "tiktok": {
                "text": "Donut gebu leleh panas berasap! #doh #sedap",
                "media_aspect_ratio": "9:16",
                "media_duration_seconds": 35.0,
            },
            "instagram": {
                "text": "Crispy caramel glaze freshly drizzled! #dohnut #foodie #dessert",
                "media_aspect_ratio": "9:16",
                "media_duration_seconds": 45.0,
            },
            "threads": {
                "text": "Doh-Nut batch 4 is officially out of the oven! Get yours now.",
                "media_aspect_ratio": None,
                "media_duration_seconds": None,
            },
            "facebook": {
                "text": "Selamat pagi semua! Nikmati tawaran kombo 6 biji donut gebu di cawangan kami hari ini.",
                "media_aspect_ratio": "16:9",
                "media_duration_seconds": None,
            },
            "x": {
                "text": "Fresh batch dropped! Who is craving salted caramel glaze? #dohnut #sedap",
                "media_aspect_ratio": None,
                "media_duration_seconds": 45.0,
            },
            "youtube": {
                "text": "Donut Glazing ASMR That Will Make You Drool #Shorts",
                "media_aspect_ratio": "9:16",
                "media_duration_seconds": 52.0,
            },
        }

        for platform, payload in test_matrix.items():
            result = SocialValidator.validate_post(
                platform=platform,
                text=payload["text"],
                media_aspect_ratio=payload["media_aspect_ratio"],
                media_duration_seconds=payload["media_duration_seconds"],
            )
            assert result.valid is True, f"Expected {platform} to pass, but got errors: {result.errors}"
            assert len(result.errors) == 0
            assert result.platform == platform
            assert result.char_count == len(payload["text"])
            assert result.max_chars > 0

    def test_auto_trim_cleans_at_word_boundary_without_cutting_words(self):
        """Test auto_trim trims cleanly at word boundary."""
        text = "Alpha Beta Gamma Delta Epsilon Zeta Eta Theta Iota Kappa Lambda"
        trimmed = SocialValidator.auto_trim("x", text)
        assert len(trimmed) <= 280
        # Text is already under 280, so unchanged
        assert trimmed == text

        long_text = "Word " * 70  # 350 chars
        trimmed_long = SocialValidator.auto_trim("x", long_text)
        assert len(trimmed_long) <= 280
        assert not trimmed_long.endswith("Wor")  # No partial word
        assert trimmed_long.endswith("Word")

    def test_facebook_aspect_ratios(self):
        """Test Facebook aspect ratio enforcement (16:9 and 1:1 allowed, others rejected)."""
        res_16_9 = SocialValidator.validate_post("facebook", "Post", media_aspect_ratio="16:9")
        assert res_16_9.valid

        res_1_1 = SocialValidator.validate_post("facebook", "Post", media_aspect_ratio="1:1")
        assert res_1_1.valid

        res_invalid = SocialValidator.validate_post("facebook", "Post", media_aspect_ratio="9:16")
        assert not res_invalid.valid
        assert any("aspect ratio" in err.lower() for err in res_invalid.errors)

    def test_x_hashtag_limit(self):
        """Test X enforces max 4 hashtags."""
        res_5_tags = SocialValidator.validate_post("x", "Fresh donuts #one #two #three #four #five")
        assert not res_5_tags.valid
        assert any("hashtag" in err.lower() or "4" in err for err in res_5_tags.errors)

        res_4_tags = SocialValidator.validate_post("x", "Fresh donuts #one #two #three #four")
        assert res_4_tags.valid

    def test_unsupported_platform_returns_invalid_result(self):
        """Test unsupported platform returns valid=False with error message."""
        res = SocialValidator.validate_post("myspace", "Hello world")
        assert not res.valid
        assert any("unsupported platform" in err.lower() for err in res.errors)

    def test_case_insensitive_platform_names(self):
        """Test platform normalization handles uppercase and leading/trailing whitespace."""
        res = SocialValidator.validate_post("  TIKTOK  ", "Donut #sedap", media_aspect_ratio="9:16")
        assert res.valid
        assert res.platform == "tiktok"

    def test_instance_and_class_method_compatibility(self):
        """Test SocialValidator can be called both on the class and on an instance."""
        validator_instance = SocialValidator()
        res_inst = validator_instance.validate_post("x", "Hello #donut")
        res_cls = SocialValidator.validate_post("x", "Hello #donut")

        assert res_inst.valid == res_cls.valid
        assert res_inst.char_count == res_cls.char_count
