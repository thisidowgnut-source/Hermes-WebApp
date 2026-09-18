"""Khairul Aming Viral & FYP Certainty Engine.

Provides automated social media viral scoring, retention linting, and 4-phase
Khairul Aming playbook generation for Doh-Nut operations.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

DEFAULT_PLAYBOOK_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "viral_playbook.json"
)

DEFAULT_PLAYBOOK: Dict[str, Any] = {
    "hooks": {
        "question_curiosity": [
            "Ramai yang tanya kenapa donut kitorang tak pernah kempis lepas sejuk...",
            "Korang tahu tak kenapa donut biasa cepat lemau tapi yang ni kekal gebu?",
        ],
        "shock_diet": [
            "Jangan tengok video ni kalau korang tengah diet atau lapar...",
            "Tolong jangan salahkan kitorang kalau korang termimpi-mimpi donut ni malam nanti...",
        ],
        "behind_the_scenes_secret": [
            "Rahsia doh gebu 48 jam yang bakeri lain takkan bagitahu korang...",
            "Hari ni saya buka rahsia macam mana kitorang bancuh filling karamel leleh...",
        ],
        "asmr_crunch": [
            "Dengar bunyi kerak rangup ni bila disira gula panas...",
            "Dengar betul-betul bila donut ni dipotong dua... gebu lembut macam kapas.",
        ],
    },
    "sensory_words": [
        "gebu",
        "rangup",
        "leleh",
        "karamel",
        "panas",
        "uli",
        "mentega",
        "coklat",
        "sira",
        "lembut",
        "berasap",
        "tarik",
    ],
    "storytelling_arcs": {
        "struggle_mastery": "Saya mula berniaga donut ni dari dapur rumah kecil...",
        "customer_craving": "Pagi tadi ada akak ni datang jauh dari Bangi semata-mata nak rasa...",
        "raw_kitchen_transparency": "Hari ni saya tunjuk dapur sebenar kitorang...",
    },
    "comment_loops": [
        "Korang team Kuih Burger donut atau team Matcha White Choco?",
        "Antara rangup di luar dengan gebu di dalam, korang prefer yang mana?",
        "Tag kawan korang yang kalau nampak donut macam ni terus hilang diet!",
    ],
    "scarcity_triggers": [
        "Batch petang ni kita goreng 50 kotak je panas-panas...",
        "Siapa cepat dia dapat untuk drop petang ni...",
    ],
    "trending_audio": [
        {
            "id": "ka_acoustic_folk",
            "title": "Khairul Aming Kitchen Acoustic (Warm Wholesome)",
            "artist": "Acoustic Fingerstyle Chill",
            "bpm": 110,
            "recommended_for": ["struggle_mastery", "behind_the_scenes_secret"],
            "audio_cue": "0:00-0:03 Senyap (Focus on Voiceover Hook) -> 0:03 Acoustic guitar masuk perlahan -> 0:15 Crescendo semasa leleh karamel",
        },
        {
            "id": "asmr_binaural_crunch",
            "title": "Binaural Foodie ASMR Beats",
            "artist": "Lo-Fi Glaze Drip Studio",
            "bpm": 88,
            "recommended_for": ["asmr_crunch"],
            "audio_cue": "0:00-0:04 Pure Crunch ASMR (Tiada Muzik) -> 0:04 Lo-fi kick & deep bassline drop semasa doh dipotong",
        },
        {
            "id": "pasar_malam_funk",
            "title": "Pasar Malam Groovy Funk Pop",
            "artist": "KL City Vibes",
            "bpm": 128,
            "recommended_for": ["customer_craving", "raw_kitchen_transparency"],
            "audio_cue": "Beat drop pada saat ke-3 sejajar dengan teks hook popping on screen",
        },
        {
            "id": "melayu_klasik_lofi",
            "title": "Nostalgia Malaya Klasik Lo-Fi",
            "artist": "Malaya Vinyl Beats",
            "bpm": 85,
            "recommended_for": ["struggle_mastery"],
            "audio_cue": "Bunyi jarum piring hitam vintage -> Rentak santai mengiringi uli doh mentega",
        },
    ],
}

HOOK_TRIGGER_KEYWORDS: List[str] = [
    "ramai yang tanya",
    "korang tahu tak",
    "jangan tengok",
    "tengah diet",
    "tolong jangan salahkan",
    "termimpi-mimpi",
    "rahsia doh",
    "rahsia",
    "takkan bagitahu",
    "buka rahsia",
    "dengar bunyi",
    "dengar betul-betul",
    "tak pernah kempis",
    "cepat lemau",
    "kekal gebu",
    "kerak rangup",
    "bila disira",
    "dipotong dua",
]

SCARCITY_KEYWORDS: List[str] = [
    "50 kotak",
    "kotak je",
    "siapa cepat",
    "siapa cepat dia dapat",
    "drop petang",
    "sold out",
    "habis",
    "terhad",
    "tinggal sikit",
    "cepat dapat",
    "batch petang",
    "sebelum habis",
    "panas-panas",
]


class ViralScore(BaseModel):
    """Pydantic model representing viral evaluation metrics (0-100)."""

    hook_score: int = Field(default=0, ge=0, le=25, description="3-second hook strength (0-25)")
    sensory_score: int = Field(
        default=0, ge=0, le=20, description="Sensory and appetite trigger word count (0-20)"
    )
    pacing_score: int = Field(
        default=0, ge=0, le=20, description="Words-per-sentence brevity and pacing (0-20)"
    )
    engagement_score: int = Field(
        default=0, ge=0, le=20, description="Debate loop / comment question presence (0-20)"
    )
    scarcity_score: int = Field(
        default=0, ge=0, le=15, description="Scarcity and FOMO urgency triggers (0-15)"
    )
    total_score: int = Field(
        default=0, ge=0, le=100, description="Aggregate score (0-100)"
    )
    is_fyp_ready: bool = Field(
        default=False, description="True if total_score >= 85 (Certified FYP Ready)"
    )
    suggestions: List[str] = Field(
        default_factory=list, description="Actionable replacement advice if total_score < 85"
    )


def load_playbook(path: Union[str, Path, None] = None) -> Dict[str, Any]:
    """Load viral playbook config from file or return default fallback."""
    target_path = Path(path) if path else DEFAULT_PLAYBOOK_PATH
    if target_path.is_file():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return DEFAULT_PLAYBOOK


def calculate_viral_score(
    text: str, playbook: Optional[Dict[str, Any]] = None
) -> ViralScore:
    """Calculate the viral score (0-100) for a given text caption or script.

    Scoring criteria:
    - 3s hook keywords/phrases: up to 25 pts.
    - Sensory keywords: 4 pts per sensory word found, max 20 pts.
    - Pacing/brevity: words per sentence <= 14 awards 20 pts, 15-20 awards 12 pts, >20 awards 5 pts.
    - Comment question/loop (?): awards 20 pts.
    - Scarcity/urgency keywords: awards 15 pts.
    - If total_score < 85, populates suggestions with actionable replacement advice.
    """
    pb = playbook or load_playbook()
    text_lower = text.lower().strip()

    if not text_lower:
        return ViralScore(
            hook_score=0,
            sensory_score=0,
            pacing_score=0,
            engagement_score=0,
            scarcity_score=0,
            total_score=0,
            is_fyp_ready=False,
            suggestions=["Teks kosong. Sila masukkan skrip atau kapsyen untuk dinilai."],
        )

    # 1. Hook Score (0-25 pts)
    hook_score = 0
    all_hook_phrases: List[str] = []
    for cat_hooks in pb.get("hooks", {}).values():
        if isinstance(cat_hooks, list):
            all_hook_phrases.extend(cat_hooks)

    # Check for presence of playbook hook phrases or hook triggers
    matched_hook = False
    for hook_phrase in all_hook_phrases:
        if hook_phrase.lower().strip(". ") in text_lower:
            matched_hook = True
            break

    if not matched_hook:
        for trigger in HOOK_TRIGGER_KEYWORDS:
            if trigger in text_lower:
                matched_hook = True
                break

    if matched_hook:
        hook_score = 25

    # 2. Sensory Score (0-20 pts: 4 pts per sensory word found, max 20)
    sensory_words = pb.get("sensory_words", DEFAULT_PLAYBOOK["sensory_words"])
    found_sensory: set[str] = set()

    for word in sensory_words:
        w_lower = word.lower()
        if w_lower == "uli":
            # Avoid false positives like 'kualiti'
            pattern = r"\b(?:di|meng)?uli(?:kan|lah)?\b"
        elif w_lower == "leleh":
            pattern = r"\b(?:me)?leleh(?:kan|nya)?\b"
        elif w_lower == "panas":
            pattern = r"\bpanas(?:-panas)?\b"
        elif w_lower == "sira":
            pattern = r"\b(?:di)?sira\b"
        elif w_lower == "berasap":
            pattern = r"\b(?:ber)?asap\b"
        elif w_lower == "tarik":
            pattern = r"\b(?:di|men)?tarik\b"
        else:
            pattern = r"\b" + re.escape(w_lower) + r"\b"

        if re.search(pattern, text_lower):
            found_sensory.add(w_lower)

    sensory_score = min(len(found_sensory) * 4, 20)

    # 3. Pacing Score (0-20 pts)
    raw_sentences = [s.strip() for s in re.split(r"[.!?\n]+", text) if s.strip()]
    sentence_word_counts = [len(s.split()) for s in raw_sentences if len(s.split()) > 0]

    if not sentence_word_counts:
        pacing_score = 0
    else:
        avg_wps = sum(sentence_word_counts) / len(sentence_word_counts)
        if avg_wps <= 14.0:
            pacing_score = 20
        elif avg_wps <= 20.0:
            pacing_score = 12
        else:
            pacing_score = 5

    # 4. Engagement Score (0-20 pts)
    has_question_mark = "?" in text
    has_comment_loop = False
    for loop in pb.get("comment_loops", []):
        if loop.lower().strip(". ?") in text_lower:
            has_comment_loop = True
            break

    if has_question_mark or has_comment_loop or "tag kawan" in text_lower:
        engagement_score = 20
    else:
        engagement_score = 0

    # 5. Scarcity Score (0-15 pts)
    has_scarcity = False
    for trigger in pb.get("scarcity_triggers", []):
        if trigger.lower().strip(". ") in text_lower:
            has_scarcity = True
            break

    if not has_scarcity:
        for kw in SCARCITY_KEYWORDS:
            if kw in text_lower:
                has_scarcity = True
                break

    if has_scarcity:
        scarcity_score = 15
    else:
        scarcity_score = 0

    # Total score calculation
    total_score = min(
        100,
        max(
            0,
            hook_score + sensory_score + pacing_score + engagement_score + scarcity_score,
        ),
    )
    is_fyp_ready = total_score >= 85

    # Actionable suggestions from Khairul Aming playbook
    suggestions: List[str] = []
    if total_score < 85:
        if hook_score < 25:
            suggestions.append(
                "Hook 3 saat lemah. Mulakan kapsyen/video dengan soalan provokatif atau amaran diet KA "
                "(cth: 'Jangan tengok video ni kalau korang tengah diet...' atau 'Rahsia doh gebu 48 jam yang bakeri lain takkan bagitahu korang...')."
            )
        if sensory_score < 20:
            missing_count = 5 - (sensory_score // 4)
            suggestions.append(
                f"Kurang perkataan deria rasa. Tambah sekurang-kurangnya {missing_count} lagi perkataan deria selera KA: "
                "'gebu', 'rangup', 'leleh', 'karamel', 'panas', atau 'lembut'."
            )
        if pacing_score < 20:
            suggestions.append(
                "Pacing ayat terlalu panjang (purata >14 patah perkataan per ayat). "
                "Pecahkan kepada ayat pendek 8-12 patah perkataan untuk ritma tontonan video pantas."
            )
        if engagement_score < 20:
            suggestions.append(
                "Tiada comment loop atau soalan interaktif (?). Tambah soalan pilihan atau debat di hujung kapsyen "
                "(cth: 'Korang team Kuih Burger donut atau team Matcha White Choco?')."
            )
        if scarcity_score < 15:
            suggestions.append(
                "Tiada elemen kelangkaan/scarcity. Masukkan FOMO terhad KA seperti: "
                "'Batch petang ni kita goreng 50 kotak je panas-panas... Siapa cepat dia dapat!'."
            )

    return ViralScore(
        hook_score=hook_score,
        sensory_score=sensory_score,
        pacing_score=pacing_score,
        engagement_score=engagement_score,
        scarcity_score=scarcity_score,
        total_score=total_score,
        is_fyp_ready=is_fyp_ready,
        suggestions=suggestions,
    )


def generate_ka_campaign(
    product_name: str, key_feature: str, arc_type: str = "struggle_mastery"
) -> Dict[str, Any]:
    """Generate a full 4-phase Khairul Aming viral campaign script and caption.

    Phases:
    1. hook_3s
    2. story_relatable
    3. climax_asmr
    4. organic_scarcity_cta
    Plus full_caption and viral_score evaluation.
    """
    playbook = load_playbook()

    # 1. 3-Second Hook
    shock_hooks = playbook.get("hooks", {}).get("shock_diet", [])
    hook_3s = (
        shock_hooks[0]
        if shock_hooks
        else "Jangan tengok video ni kalau korang tengah diet atau lapar..."
    )

    # 2. Relatable Storytelling Arc
    arcs = playbook.get("storytelling_arcs", {})
    arc_base = arcs.get(
        arc_type,
        arcs.get(
            "struggle_mastery",
            "Saya mula berniaga donut ni dari dapur rumah kecil...",
        ),
    )
    story_relatable = (
        f"{arc_base} Setiap hari kami uli doh {product_name} dengan mentega asli dan {key_feature}."
    )

    # 3. ASMR Climax
    climax_asmr = (
        "Dengar bunyi kerak rangup ni bila disira gula panas! "
        "Bila dipotong dua, karamel leleh coklat pekat panas-panas meleleh gebu lembut macam kapas."
    )

    # 4. Organic Scarcity & Comment Loop CTA
    scarcity_list = playbook.get("scarcity_triggers", [])
    scarcity_line = (
        scarcity_list[0]
        if scarcity_list
        else "Batch petang ni kita goreng 50 kotak je panas-panas..."
    )

    comment_loops = playbook.get("comment_loops", [])
    comment_line = (
        comment_loops[0]
        if comment_loops
        else "Korang team Kuih Burger donut atau team Matcha White Choco?"
    )

    organic_scarcity_cta = (
        f"{scarcity_line} Siapa cepat dia dapat untuk drop petang ni!\n\n{comment_line}"
    )

    # Combined Full Caption
    full_caption = (
        f"{hook_3s}\n\n{story_relatable}\n\n{climax_asmr}\n\n{organic_scarcity_cta}"
    )

    # Evaluate Viral Score
    viral_score = calculate_viral_score(full_caption, playbook=playbook)

    # 5. Malaysian Trending Audio & Sound Cue Attachment
    trending_audios = playbook.get("trending_audio", [])
    selected_audio = None
    for audio in trending_audios:
        if arc_type in audio.get("recommended_for", []):
            selected_audio = audio
            break
    if not selected_audio and trending_audios:
        selected_audio = trending_audios[0]

    return {
        "hook_3s": hook_3s,
        "story_relatable": story_relatable,
        "climax_asmr": climax_asmr,
        "organic_scarcity_cta": organic_scarcity_cta,
        "full_caption": full_caption,
        "viral_score": viral_score,
        "recommended_audio": selected_audio,
    }

