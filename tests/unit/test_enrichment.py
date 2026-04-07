"""Unit tests for metadata enrichment in mrag.data.enrichment."""

from mrag.data.models import Difficulty, DocumentMetadata, QuestionType


class TestQuestionTypeClassifier:
    def test_who_pattern_factoid(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert classify_question_type("Who is Einstein?") == QuestionType.FACTOID

    def test_what_pattern_factoid(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert classify_question_type("What is photosynthesis?") == QuestionType.FACTOID

    def test_when_pattern_factoid(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert classify_question_type("When did WWII end?") == QuestionType.FACTOID

    def test_where_pattern_factoid(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert classify_question_type("Where is Paris?") == QuestionType.FACTOID

    def test_which_pattern_factoid(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert (
            classify_question_type("Which planet is largest?") == QuestionType.FACTOID
        )

    def test_how_many_pattern_factoid(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert (
            classify_question_type("How many bones in the body?")
            == QuestionType.FACTOID
        )

    def test_how_much_pattern_factoid(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert classify_question_type("How much does it cost?") == QuestionType.FACTOID

    def test_is_pattern_yes_no(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert classify_question_type("Is the Earth flat?") == QuestionType.YES_NO

    def test_are_pattern_yes_no(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert classify_question_type("Are dogs mammals?") == QuestionType.YES_NO

    def test_was_pattern_yes_no(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert classify_question_type("Was Lincoln a president?") == QuestionType.YES_NO

    def test_do_does_pattern_yes_no(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert classify_question_type("Do fish swim?") == QuestionType.YES_NO
        assert classify_question_type("Does water boil at 100C?") == QuestionType.YES_NO

    def test_can_could_pattern_yes_no(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert classify_question_type("Can birds fly?") == QuestionType.YES_NO

    def test_explain_pattern_descriptive(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert (
            classify_question_type("Explain the theory of evolution.")
            == QuestionType.DESCRIPTIVE
        )

    def test_describe_pattern_descriptive(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert (
            classify_question_type("Describe the water cycle.")
            == QuestionType.DESCRIPTIVE
        )

    def test_why_pattern_descriptive(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert (
            classify_question_type("Why is the sky blue?") == QuestionType.DESCRIPTIVE
        )

    def test_how_does_pattern_descriptive(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert (
            classify_question_type("How does the heart pump blood?")
            == QuestionType.DESCRIPTIVE
        )

    def test_list_pattern(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert (
            classify_question_type("List the planets in the solar system.")
            == QuestionType.LIST
        )

    def test_name_pattern_list(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert classify_question_type("Name all the continents.") == QuestionType.LIST

    def test_unknown_pattern(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert classify_question_type("Tell me about rivers.") == QuestionType.UNKNOWN

    def test_case_insensitive(self) -> None:
        from mrag.data.enrichment import classify_question_type

        assert classify_question_type("who is einstein?") == QuestionType.FACTOID
        assert classify_question_type("IS THIS REAL?") == QuestionType.YES_NO


class TestDomainClassifier:
    def test_science_domain(self) -> None:
        from mrag.data.enrichment import classify_domain

        result = classify_domain(
            "What is photosynthesis?",
            "A process in plants",
            "Photosynthesis is a biological process.",
        )
        assert result == "science"

    def test_history_domain(self) -> None:
        from mrag.data.enrichment import classify_domain

        result = classify_domain(
            "When did WWII end?",
            "1945",
            "World War II ended in 1945.",
        )
        assert result == "history"

    def test_geography_domain(self) -> None:
        from mrag.data.enrichment import classify_domain

        result = classify_domain(
            "Where is the Eiffel Tower?",
            "Paris",
            "The Eiffel Tower is in Paris, France.",
        )
        assert result == "geography"

    def test_health_domain(self) -> None:
        from mrag.data.enrichment import classify_domain

        result = classify_domain(
            "How many bones in the body?",
            "206",
            "The adult skeleton has 206 bones.",
        )
        assert result == "health"

    def test_default_general_domain(self) -> None:
        from mrag.data.enrichment import classify_domain

        result = classify_domain("Something unusual?", "Answer", "Some text here.")
        assert isinstance(result, str)
        assert len(result) > 0


class TestDifficultyScorer:
    def test_easy_with_short_answer(self) -> None:
        from mrag.data.enrichment import score_difficulty

        result = score_difficulty(
            "What is X?",
            short_answer="X is Y",
            answer_long="X is Y because Z.",
        )
        assert result == Difficulty.EASY

    def test_medium_no_short_answer(self) -> None:
        from mrag.data.enrichment import score_difficulty

        result = score_difficulty(
            "Explain X.",
            short_answer=None,
            answer_long="X is something complex.",
        )
        assert result == Difficulty.MEDIUM

    def test_hard_ambiguous(self) -> None:
        from mrag.data.enrichment import score_difficulty

        result = score_difficulty(
            "What is the meaning of life?",
            short_answer=None,
            answer_long="The meaning of life is a philosophical question.",
        )
        # Should be medium or hard since no short answer
        assert result in (Difficulty.MEDIUM, Difficulty.HARD)


class TestEnrich:
    def test_enrich_factoid_with_short_answer(self) -> None:
        from mrag.data.enrichment import enrich

        meta = enrich(
            question="Who is Einstein?",
            answer_short="A physicist",
            answer_long="Albert Einstein was a theoretical physicist.",
        )
        assert isinstance(meta, DocumentMetadata)
        assert meta.question_type == QuestionType.FACTOID
        assert meta.has_short_answer is True
        assert meta.difficulty == Difficulty.EASY
        assert meta.domain != ""
        assert meta.source_id != ""

    def test_enrich_descriptive_without_short_answer(self) -> None:
        from mrag.data.enrichment import enrich

        meta = enrich(
            question="Explain the theory of evolution.",
            answer_short=None,
            answer_long="Evolution is the change in heritable characteristics.",
        )
        assert meta.question_type == QuestionType.DESCRIPTIVE
        assert meta.has_short_answer is False
        assert meta.difficulty == Difficulty.MEDIUM

    def test_enrich_deterministic(self) -> None:
        from mrag.data.enrichment import enrich

        args = ("What is water?", "H2O", "Water is a transparent fluid.")
        m1 = enrich(*args)
        m2 = enrich(*args)
        assert m1.question_type == m2.question_type
        assert m1.domain == m2.domain
        assert m1.difficulty == m2.difficulty
