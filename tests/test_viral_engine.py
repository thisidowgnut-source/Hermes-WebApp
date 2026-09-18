"""Tests for Khairul Aming Viral & FYP Certainty Engine."""
from pathlib import Path
import pytest

from backend.services.viral_engine import (
    ViralScore,
    load_playbook,
    calculate_viral_score,
    generate_ka_campaign,
)


def test_load_playbook_default():
    """Verify that load_playbook loads the default configuration properly."""
    playbook = load_playbook()
    assert "hooks" in playbook
    assert "sensory_words" in playbook
    assert "storytelling_arcs" in playbook
    assert "comment_loops" in playbook
    assert "scarcity_triggers" in playbook
    assert "question_curiosity" in playbook["hooks"]
    assert "gebu" in playbook["sensory_words"]


def test_load_playbook_custom_path(tmp_path: Path):
    """Verify loading from a custom path."""
    custom_file = tmp_path / "custom_playbook.json"
    custom_file.write_text(
        '{"hooks": {}, "sensory_words": ["gebu"], "storytelling_arcs": {}, "comment_loops": [], "scarcity_triggers": []}',
        encoding="utf-8",
    )
    loaded = load_playbook(custom_file)
    assert loaded["sensory_words"] == ["gebu"]


def test_generic_boring_corporate_text_scores_low():
    """Test generic boring corporate text scores < 60 and is_fyp_ready is False."""
    boring_text = (
        "Kami dari syarikat korporat Doh-Nut Sdn Bhd mengeluarkan pelbagai produk pastri berkualiti "
        "tinggi mengikut piawaian industri standard ISO yang disahkan. Sila layari portal rasmi kami "
        "untuk mendapatkan maklumat korporat dan membuat pesanan perniagaan borong."
    )
    score: ViralScore = calculate_viral_score(boring_text)
    assert score.total_score < 60
    assert score.is_fyp_ready is False
    assert isinstance(score.suggestions, list)
    assert len(score.suggestions) > 0


def test_khairul_aming_structured_text_scores_high():
    """Test Khairul Aming structured text scores >= 85 and is_fyp_ready is True."""
    ka_text = (
        "Jangan tengok video ni kalau korang tengah diet atau lapar...\n\n"
        "Saya mula berniaga donut ni dari dapur rumah kecil. "
        "Setiap hari kami uli doh dengan mentega asli dan coklat pekat.\n\n"
        "Dengar bunyi kerak rangup ni bila disira gula panas! "
        "Bila dipotong dua, karamel leleh keluar panas-panas, lembut gebu macam kapas.\n\n"
        "Batch petang ni kita goreng 50 kotak je panas-panas... Siapa cepat dia dapat untuk drop petang ni!\n\n"
        "Korang team Kuih Burger donut atau team Matcha White Choco?"
    )
    score: ViralScore = calculate_viral_score(ka_text)
    assert score.total_score >= 85
    assert score.is_fyp_ready is True
    assert score.hook_score == 25
    assert score.sensory_score >= 16
    assert score.pacing_score == 20
    assert score.engagement_score == 20
    assert score.scarcity_score == 15
    assert score.suggestions == []


def test_generate_ka_campaign_returns_valid_structure_and_high_score():
    """Test generate_ka_campaign returns valid structure and viral_score.total_score >= 85."""
    campaign = generate_ka_campaign(
        product_name="Doh-Nut Salted Caramel",
        key_feature="inti karamel leleh 48 jam",
        arc_type="struggle_mastery",
    )
    assert "hook_3s" in campaign
    assert "story_relatable" in campaign
    assert "climax_asmr" in campaign
    assert "organic_scarcity_cta" in campaign
    assert "full_caption" in campaign
    assert "viral_score" in campaign

    viral_score = campaign["viral_score"]
    assert isinstance(viral_score, ViralScore)
    assert viral_score.total_score >= 85
    assert viral_score.is_fyp_ready is True
    assert len(campaign["full_caption"]) > 50


def test_generate_ka_campaign_different_arcs():
    """Test campaign generation across all available storytelling arcs."""
    arcs = ["struggle_mastery", "customer_craving", "raw_kitchen_transparency"]
    for arc in arcs:
        campaign = generate_ka_campaign(
            product_name="Doh-Nut Berasap",
            key_feature="doh gebu mentega",
            arc_type=arc,
        )
        assert campaign["viral_score"].total_score >= 85
        assert campaign["viral_score"].is_fyp_ready is True


def test_suggestions_are_returned_when_score_below_85():
    """Test suggestions are returned when score is below 85."""
    partial_text = "Donut kami sedap gebu lembut leleh dimakan bersama teh."
    score = calculate_viral_score(partial_text)
    assert score.total_score < 85
    assert score.is_fyp_ready is False
    assert len(score.suggestions) > 0
    # Should suggest hook, pacing or scarcity/engagement improvements
    suggestions_text = " ".join(score.suggestions)
    assert "Hook" in suggestions_text or "soalan" in suggestions_text or "scarcity" in suggestions_text.lower()


def test_generate_ka_campaign_trending_audio():
    """Test campaign generation attaches appropriate Malaysian trending audio and audio cues."""
    campaign = generate_ka_campaign(
        product_name="Doh-Nut Berderap",
        key_feature="karamel leleh",
        arc_type="struggle_mastery",
    )
    assert "recommended_audio" in campaign
    audio = campaign["recommended_audio"]
    assert audio is not None
    assert "title" in audio
    assert "artist" in audio
    assert "bpm" in audio
    assert "audio_cue" in audio
    assert audio["bpm"] > 0
    assert len(audio["audio_cue"]) > 10

