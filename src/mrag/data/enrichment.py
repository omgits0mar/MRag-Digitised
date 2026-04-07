"""Metadata enrichment for question-answer pairs.

Provides rule-based classifiers for question type, domain, and difficulty.
All classifiers are deterministic and offline-capable.
"""

from __future__ import annotations

import re
import uuid

import structlog

from mrag.data.models import Difficulty, DocumentMetadata, QuestionType

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Question type classifier (T010)
# ---------------------------------------------------------------------------

_FACTOID_PATTERNS = [
    re.compile(r"^(who|what|when|where|which)\b", re.IGNORECASE),
    re.compile(r"^how (many|much)\b", re.IGNORECASE),
]

_YES_NO_PATTERNS = [
    re.compile(
        r"^(is|are|was|were|do|does|did|can|could|"
        r"will|would|should|has|have|had)\b",
        re.IGNORECASE,
    ),
]

_LIST_PATTERNS = [
    re.compile(r"^(list|name)\s+(all|some|the|every)?\s*", re.IGNORECASE),
]

_DESCRIPTIVE_PATTERNS = [
    re.compile(r"^(explain|describe)\b", re.IGNORECASE),
    re.compile(r"^why\b", re.IGNORECASE),
    re.compile(r"^how (does|do|is|are|can|could|should)\b", re.IGNORECASE),
]


def classify_question_type(question: str) -> QuestionType:
    """Classify question type based on linguistic patterns.

    Args:
        question: The question text.

    Returns:
        QuestionType enum value.
    """
    q = question.strip()
    if not q:
        return QuestionType.UNKNOWN

    for pattern in _DESCRIPTIVE_PATTERNS:
        if pattern.match(q):
            return QuestionType.DESCRIPTIVE

    for pattern in _LIST_PATTERNS:
        if pattern.match(q):
            return QuestionType.LIST

    for pattern in _YES_NO_PATTERNS:
        if pattern.match(q):
            return QuestionType.YES_NO

    for pattern in _FACTOID_PATTERNS:
        if pattern.match(q):
            return QuestionType.FACTOID

    return QuestionType.UNKNOWN


# ---------------------------------------------------------------------------
# Domain classifier (T011)
# ---------------------------------------------------------------------------

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "science": [
        "physics",
        "chemistry",
        "biology",
        "atom",
        "molecule",
        "cell",
        "dna",
        "energy",
        "force",
        "gravity",
        "experiment",
        "hypothesis",
        "photosynthesis",
        "evolution",
        "chemical",
        "element",
        "compound",
        "reaction",
        "organism",
        "species",
        "theory",
        "scientific",
        "quantum",
        "electron",
        "proton",
        "neutron",
        "nucleus",
        "genome",
    ],
    "history": [
        "war",
        "battle",
        "empire",
        "king",
        "queen",
        "revolution",
        "century",
        "dynasty",
        "colonial",
        "independence",
        "treaty",
        "civilization",
        "ancient",
        "medieval",
        "president",
        "election",
        "democracy",
        "monarchy",
        "conquest",
        "invasion",
        "treaty",
        "world war",
        "soldier",
        "army",
        "military",
        "political",
    ],
    "geography": [
        "country",
        "city",
        "continent",
        "ocean",
        "mountain",
        "river",
        "island",
        "desert",
        "climate",
        "population",
        "capital",
        "border",
        "region",
        "territory",
        "latitude",
        "longitude",
        "hemisphere",
        "equator",
        "plateau",
        "valley",
        "volcano",
        "earthquake",
        "tsunami",
        "eiffel",
        "tower",
        "paris",
    ],
    "health": [
        "disease",
        "medicine",
        "doctor",
        "hospital",
        "treatment",
        "symptom",
        "diagnosis",
        "surgery",
        "vaccine",
        "virus",
        "bacteria",
        "infection",
        "heart",
        "brain",
        "blood",
        "bone",
        "muscle",
        "organ",
        "cancer",
        "diabetes",
        "immune",
        "nutrition",
        "vitamin",
        "protein",
        "diet",
    ],
    "technology": [
        "computer",
        "software",
        "internet",
        "algorithm",
        "data",
        "programming",
        "digital",
        "electronic",
        "artificial intelligence",
        "machine learning",
        "robot",
        "processor",
        "memory",
        "network",
        "database",
        "cloud",
        "cybersecurity",
        "encryption",
    ],
    "mathematics": [
        "equation",
        "formula",
        "theorem",
        "proof",
        "calculus",
        "algebra",
        "geometry",
        "statistics",
        "probability",
        "integral",
        "derivative",
        "matrix",
        "vector",
        "function",
        "number",
        "fraction",
        "decimal",
        "percentage",
    ],
}


def classify_domain(question: str, answer_short: str | None, answer_long: str) -> str:
    """Classify the domain of a question-answer pair using keyword matching.

    Args:
        question: Question text.
        answer_short: Short answer (may be None).
        answer_long: Long answer text.

    Returns:
        Domain string (e.g., "science", "history").
    """
    combined = f"{question} {answer_short or ''} {answer_long}".lower()
    scores: dict[str, int] = {}

    for domain, keywords in _DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[domain] = score

    if not scores:
        return "general"

    return max(scores, key=lambda d: scores[d])


# ---------------------------------------------------------------------------
# Difficulty scorer (T012)
# ---------------------------------------------------------------------------


def score_difficulty(
    question: str, short_answer: str | None, answer_long: str
) -> Difficulty:
    """Score the difficulty of a question-answer pair.

    Args:
        question: Question text.
        short_answer: Short answer if available.
        answer_long: Long answer text.

    Returns:
        Difficulty enum value.
    """
    has_short = short_answer is not None and short_answer.strip() != ""

    if has_short:
        return Difficulty.EASY

    # Check for ambiguous or very long answers
    long_tokens = len(answer_long.split())
    question_type = classify_question_type(question)

    if question_type == QuestionType.DESCRIPTIVE and long_tokens > 100:
        return Difficulty.HARD

    return Difficulty.MEDIUM


# ---------------------------------------------------------------------------
# Combined enrich function (T012)
# ---------------------------------------------------------------------------


def enrich(
    question: str,
    answer_short: str | None,
    answer_long: str,
) -> DocumentMetadata:
    """Classify and enrich a question-answer pair with metadata.

    Args:
        question: Question text.
        answer_short: Short answer (may be None).
        answer_long: Long answer text.

    Returns:
        DocumentMetadata with all fields populated.
    """
    question_type = classify_question_type(question)
    domain = classify_domain(question, answer_short, answer_long)
    difficulty = score_difficulty(question, answer_short, answer_long)
    has_short_answer = answer_short is not None and answer_short.strip() != ""
    source_id = str(uuid.uuid4())

    return DocumentMetadata(
        question_type=question_type,
        domain=domain,
        difficulty=difficulty,
        has_short_answer=has_short_answer,
        source_id=source_id,
        language="en",
    )
