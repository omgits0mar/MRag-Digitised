"""Shared test fixtures for MRAG test suite."""

from typing import Any

import pytest


@pytest.fixture()
def temp_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Provide temporary environment variable overrides.

    Returns a dict that can be used to set env vars via monkeypatch.
    Automatically cleans up after the test.
    """
    overrides: dict[str, str] = {}
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)
    return overrides


@pytest.fixture()
def temp_dir(tmp_path: Any) -> Any:
    """Provide a temporary directory that is cleaned up after the test."""
    return tmp_path


@pytest.fixture()
def sample_config_dict() -> dict[str, Any]:
    """Provide a sample configuration dictionary with all required fields."""
    return {
        "app_name": "mrag",
        "app_version": "0.1.0",
        "debug": False,
        "log_level": "INFO",
        "embedding_model_name": "paraphrase-multilingual-MiniLM-L12-v2",
        "embedding_dimension": 384,
        "chunk_size": 512,
        "chunk_overlap": 50,
        "top_k": 5,
        "faiss_index_type": "Flat",
        "llm_api_url": "https://api.groq.com/openai/v1",
        "llm_api_key": "test-key-for-unit-tests",
        "llm_model_name": "llama3-8b-8192",
        "llm_temperature": 0.1,
        "llm_max_tokens": 1024,
        "database_url": "sqlite:///test.db",
        "cache_ttl_seconds": 3600,
        "cache_max_size": 1000,
        "data_dir": "data",
        "prompts_dir": "prompts/templates",
    }


# ---------------------------------------------------------------------------
# Phase 1 — RAG Pipeline Fixtures
# ---------------------------------------------------------------------------

SAMPLE_CSV_ROWS: list[dict[str, str]] = [
    {
        "question_text": "Who is Albert Einstein?",
        "short_answer": "A German-born theoretical physicist",
        "long_answer": (
            "Albert Einstein was a German-born theoretical physicist who is"
            " widely held to be one of the greatest and most influential"
            " scientists of all time. He developed the theory of relativity,"
            " one of the two pillars of modern physics."
        ),
        "document_title": "Albert Einstein - Wikipedia",
        "document_url": "https://en.wikipedia.org/wiki/Albert_Einstein",
    },
    {
        "question_text": "What is photosynthesis?",
        "short_answer": "A process used by plants to convert light energy",
        "long_answer": (
            "Photosynthesis is a process used by plants and other organisms"
            " to convert light energy into chemical energy that, through"
            " cellular respiration, can later be released to fuel the"
            " organism's activities. This chemical energy is stored in"
            " carbohydrate molecules such as sugars, which are synthesized"
            " from carbon dioxide and water."
        ),
        "document_title": "Photosynthesis - Wikipedia",
        "document_url": "https://en.wikipedia.org/wiki/Photosynthesis",
    },
    {
        "question_text": "When did World War II end?",
        "short_answer": "September 2, 1945",
        "long_answer": (
            "World War II ended on September 2, 1945, when Japan formally"
            " surrendered aboard the USS Missouri in Tokyo Bay. The war in"
            " Europe had ended earlier, on May 8, 1945, known as V-E Day."
        ),
        "document_title": "World War II - Wikipedia",
        "document_url": "https://en.wikipedia.org/wiki/World_War_II",
    },
    {
        "question_text": "Where is the Eiffel Tower located?",
        "short_answer": "Paris, France",
        "long_answer": (
            "The Eiffel Tower is a wrought-iron lattice tower on the Champ"
            " de Mars in Paris, France. It is named after the engineer"
            " Gustave Eiffel, whose company designed and built the tower."
        ),
        "document_title": "Eiffel Tower - Wikipedia",
        "document_url": "https://en.wikipedia.org/wiki/Eiffel_Tower",
    },
    {
        "question_text": "How does the heart pump blood?",
        "short_answer": None,
        "long_answer": (
            "The heart is a muscular organ that pumps blood through the blood"
            " vessels of the circulatory system. Blood provides the body with"
            " oxygen and nutrients, as well as assists in the removal of"
            " metabolic wastes. The heart is divided into four chambers: the"
            " left and right atria, and the left and right ventricles."
        ),
        "document_title": "Heart - Wikipedia",
        "document_url": "https://en.wikipedia.org/wiki/Heart",
    },
    {
        "question_text": "Is the Earth flat?",
        "short_answer": "No",
        "long_answer": (
            "The Earth is not flat. It is an oblate spheroid, meaning it is"
            " mostly spherical but slightly flattened at the poles and bulging"
            " at the equator. This has been known since ancient Greek times"
            " and confirmed by modern science and space exploration."
        ),
        "document_title": "Spherical Earth - Wikipedia",
        "document_url": "https://en.wikipedia.org/wiki/Spherical_Earth",
    },
    {
        "question_text": "Explain the theory of evolution.",
        "short_answer": None,
        "long_answer": (
            "The theory of evolution by natural selection was first"
            " formulated in Darwin's book 'On the Origin of Species' in 1859."
            " It describes the process by which organisms change over time as"
            " a result of changes in heritable physical or behavioral traits."
            " These changes allow organisms to better adapt to their"
            " environment and help them survive and reproduce."
        ),
        "document_title": "Evolution - Wikipedia",
        "document_url": "https://en.wikipedia.org/wiki/Evolution",
    },
    {
        "question_text": "List the planets in the solar system.",
        "short_answer": "Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune",
        "long_answer": (
            "The eight planets in our solar system, in order from the Sun,"
            " are Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus,"
            " and Neptune. Pluto was reclassified as a dwarf planet in 2006"
            " by the International Astronomical Union."
        ),
        "document_title": "Solar System - Wikipedia",
        "document_url": "https://en.wikipedia.org/wiki/Solar_System",
    },
    {
        "question_text": "What causes earthquakes?",
        "short_answer": "Movement of tectonic plates",
        "long_answer": (
            "Earthquakes are caused by a sudden release of energy in the"
            " Earth's lithosphere that creates seismic waves. This energy"
            " release is usually caused by the movement of tectonic plates."
            " When plates collide, separate, or slide past each other, stress"
            " builds up until it exceeds the strength of the rock, causing"
            " a sudden release of energy."
        ),
        "document_title": "Earthquake - Wikipedia",
        "document_url": "https://en.wikipedia.org/wiki/Earthquake",
    },
    {
        "question_text": "How many bones are in the human body?",
        "short_answer": "206",
        "long_answer": (
            "The adult human skeleton consists of 206 bones. At birth, humans"
            " have around 270 soft bones, but as they grow, many of these"
            " fuse together to form the 206 bones of the adult skeleton."
        ),
        "document_title": "Human skeleton - Wikipedia",
        "document_url": "https://en.wikipedia.org/wiki/Human_skeleton",
    },
]

# Edge-case records for testing ingestion robustness
MALFORMED_CSV_ROWS: list[dict[str, str]] = [
    # Missing required fields
    {
        "question_text": "",
        "short_answer": "some answer",
        "long_answer": "",
        "document_title": "Empty fields",
        "document_url": "",
    },
    # Only whitespace in required fields
    {
        "question_text": "   ",
        "short_answer": None,
        "long_answer": "   ",
        "document_title": "Whitespace only",
        "document_url": "",
    },
    # Missing question_text column entirely (will be handled at CSV level)
    {
        "short_answer": "answer without question",
        "long_answer": "Some long answer text.",
        "document_title": "Missing question",
        "document_url": "",
    },
]


@pytest.fixture()
def sample_csv_content() -> str:
    """Return CSV-formatted string with 10 valid sample rows."""
    import io

    import pandas as pd

    df = pd.DataFrame(SAMPLE_CSV_ROWS)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


@pytest.fixture()
def sample_csv_with_malformed() -> str:
    """Return CSV with 10 valid rows followed by 3 malformed rows."""
    import io

    import pandas as pd

    df = pd.DataFrame(SAMPLE_CSV_ROWS + MALFORMED_CSV_ROWS)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


@pytest.fixture()
def sample_csv_file(tmp_path: Any) -> str:
    """Write sample CSV to a temp file and return the path."""
    import io

    import pandas as pd

    df = pd.DataFrame(SAMPLE_CSV_ROWS)
    path = tmp_path / "sample.csv"
    df.to_csv(path, index=False)
    return str(path)


@pytest.fixture()
def sample_json_file(tmp_path: Any) -> str:
    """Write sample JSON to a temp file and return the path."""
    import json

    path = tmp_path / "sample.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_CSV_ROWS, f, ensure_ascii=False, indent=2)
    return str(path)


@pytest.fixture()
def sample_long_text() -> str:
    """Return a long text suitable for chunking tests (~2000 words)."""
    return (
        "The history of science is the study of the development of science "
        "and scientific knowledge, including both the natural and social "
        "sciences. Science is a body of empirical, theoretical, and practical "
        "knowledge about the natural world, produced by scientists who "
        "emphasize the observation, explanation, and prediction of real-world "
        "phenomena. "
        "The earliest roots of science can be traced to Ancient Egypt and "
        "Mesopotamia in around 3000 to 1200 BCE. Their contributions to "
        "mathematics, astronomy, and medicine entered and shaped Greek natural "
        "philosophy of classical antiquity. "
        "After the fall of the Western Roman Empire, knowledge of Greek "
        "conceptions of the world deteriorated in Western Europe during the "
        "early centuries of the Middle Ages but was preserved in the Muslim "
        "world during the Islamic Golden Age. "
        "The recovery and assimilation of Greek works and Islamic inquiries "
        "into Western Europe from the 10th to 13th century revived the "
        "learning of natural philosophy in the West. "
        "Natural philosophy was transformed during the Scientific Revolution "
        "in 16th- and 17th-century Europe, as new ideas and discoveries "
        "departed from previous Greek conceptions and traditions. "
        "Galileo Galilei was an Italian astronomer, physicist and engineer. "
        "He has been called the father of observational astronomy, the father "
        "of modern physics, and the father of the scientific method. "
        "Isaac Newton's Principia, published in 1687, laid the foundations "
        "for classical mechanics and the law of universal gravitation. "
        "Newton also developed calculus independently of Gottfried Wilhelm "
        "Leibniz, who also made major contributions to mathematics and "
        "philosophy. "
        "During the 19th century, many new branches of science emerged. "
        "Chemistry evolved from alchemy into a systematic discipline. "
        "Michael Faraday and James Clerk Maxwell established the foundations "
        "of electromagnetic theory. "
        "Charles Darwin published On the Origin of Species in 1859, "
        "introducing the theory of evolution by natural selection. "
        "Gregor Mendel's experiments with pea plants established the "
        "principles of heredity, forming the basis of modern genetics. "
        "The 20th century brought revolutionary changes to science. "
        "Albert Einstein's theories of special and general relativity "
        "transformed our understanding of space, time, and gravity. "
        "Quantum mechanics emerged from the work of Max Planck, Niels Bohr, "
        "Werner Heisenberg, and Erwin Schrödinger, among others. "
        "The discovery of the structure of DNA by Watson and Crick in 1953 "
        "opened the field of molecular biology and modern genetics. "
        "The development of the transistor and integrated circuits led to "
        "the computer revolution and the digital age we live in today. "
        "Space exploration began with the launch of Sputnik in 1957 and "
        "culminated with the Apollo 11 Moon landing in 1969. "
        "The internet, originally developed as a military research project, "
        "transformed global communication and commerce in the 1990s and "
        "beyond. "
        "In the 21st century, advances in artificial intelligence, "
        "CRISPR gene editing, and quantum computing promise to reshape "
        "science and society once again."
    )
