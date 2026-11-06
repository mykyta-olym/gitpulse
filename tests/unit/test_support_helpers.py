"""Unit tests for support forms pure helpers - sentiment & anonymization."""

from app.services.support_forms import _anonymize_text, analyze_sentiment


class TestAnonymizeText:
    """Validate text anonymization for support processing."""

    def test_redacts_email(self) -> None:
        assert _anonymize_text("Contact john@example.com") == "Contact [EMAIL]"

    def test_redacts_mention(self) -> None:
        assert _anonymize_text("Thanks @teacher") == "Thanks [MENTION]"

    def test_redacts_url(self) -> None:
        assert _anonymize_text("See https://example.com/page") == "See [URL]"

    def test_redacts_student_id(self) -> None:
        assert _anonymize_text("Student AB12345 submitted") == "Student [ID] submitted"

    def test_multiple_redactions(self) -> None:
        text = "Email john@x.com and @teacher at https://x.com"
        result = _anonymize_text(text)
        assert "[EMAIL]" in result
        assert "[MENTION]" in result
        assert "[URL]" in result


class TestAnalyzeSentiment:
    """Validate keyword-based sentiment analysis."""

    def test_positive_text(self) -> None:
        result = analyze_sentiment("This is amazing and great")
        assert result["label"] == "positive"
        assert result["positive_count"] >= 2
        assert result["score"] > 0.2

    def test_negative_text(self) -> None:
        result = analyze_sentiment("This is terrible and broken")
        assert result["label"] == "negative"
        assert result["negative_count"] >= 2
        assert result["score"] < -0.2

    def test_neutral_text(self) -> None:
        result = analyze_sentiment("The project uses Python and SQL")
        assert result["label"] == "neutral"

    def test_empty_text(self) -> None:
        result = analyze_sentiment("")
        assert result["label"] == "neutral"
        assert result["score"] == 0.0

    def test_whitespace_text(self) -> None:
        result = analyze_sentiment("   ")
        assert result["label"] == "neutral"

    def test_mixed_sentiment(self) -> None:
        result = analyze_sentiment("Great features but slow performance")
        assert result["positive_count"] >= 1
        assert result["negative_count"] >= 1
