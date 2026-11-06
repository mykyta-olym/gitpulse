"""Tests for app.utils.text_analysis module."""


class TestWordCount:
    """Tests for word_count function."""

    def test_none_input(self) -> None:
        from app.utils.text_analysis import word_count

        result = word_count(None)
        assert result == 0

    def test_empty_string(self) -> None:
        from app.utils.text_analysis import word_count

        result = word_count("")
        assert result == 0

    def test_single_word(self) -> None:
        from app.utils.text_analysis import word_count

        result = word_count("hello")
        assert result == 1

    def test_multiple_words(self) -> None:
        from app.utils.text_analysis import word_count

        result = word_count("hello world foo bar")
        assert result == 4

    def test_extra_whitespace(self) -> None:
        from app.utils.text_analysis import word_count

        result = word_count("  hello   world  ")
        assert result == 2


class TestCharCount:
    """Tests for char_count function."""

    def test_none_input(self) -> None:
        from app.utils.text_analysis import char_count

        result = char_count(None)
        assert result == 0

    def test_empty_string(self) -> None:
        from app.utils.text_analysis import char_count

        result = char_count("")
        assert result == 0

    def test_simple_string(self) -> None:
        from app.utils.text_analysis import char_count

        result = char_count("hello")
        assert result == 5

    def test_ignores_whitespace(self) -> None:
        from app.utils.text_analysis import char_count

        result = char_count("hello world")
        # "helloworld" = 10 chars
        assert result == 10

    def test_multiple_spaces(self) -> None:
        from app.utils.text_analysis import char_count

        result = char_count("  a   b   c  ")
        assert result == 3


class TestIsMeaningfulComment:
    """Tests for is_meaningful_comment function."""

    def test_none_input(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        result = is_meaningful_comment(None)
        assert result is False

    def test_empty_string(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        result = is_meaningful_comment("")
        assert result is False

    def test_trivial_ok(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        result = is_meaningful_comment("ok")
        assert result is False

    def test_trivial_lgtm(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        result = is_meaningful_comment("LGTM")
        assert result is False

    def test_trivial_looks_good(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        result = is_meaningful_comment("looks good")
        assert result is False

    def test_trivial_plus_one(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        result = is_meaningful_comment("+1")
        assert result is False

    def test_trivial_approved(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        result = is_meaningful_comment("approved")
        assert result is False

    def test_trivial_done(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        result = is_meaningful_comment("done")
        assert result is False

    def test_short_comment(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        result = is_meaningful_comment("Fix the bug")  # 3 words < 30
        assert result is False

    def test_meaningful_comment(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        # Long comment with >= 30 words
        long_text = " ".join(["word"] * 35)
        result = is_meaningful_comment(long_text)
        assert result is True

    def test_custom_min_words(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        result = is_meaningful_comment("five words are used here", min_words=5)
        assert result is True

    def test_trivial_fixed(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        result = is_meaningful_comment("fixed")
        assert result is False

    def test_trivial_thanks(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        result = is_meaningful_comment("thanks")
        assert result is False

    def test_markdown_stripped(self) -> None:
        from app.utils.text_analysis import is_meaningful_comment

        # Markdown artifacts should be stripped before checking
        text = "> " + " ".join(["word"] * 35)
        result = is_meaningful_comment(text)
        assert result is True
