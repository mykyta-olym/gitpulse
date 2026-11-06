"""The line under the reader's name is about software, and costs nothing.

It used to be fetched from a general life-advice API, which is how a dashboard
for assessing student teamwork came to say "You will always regret the round of
Jaegermeister" - rendered "JÃ¤germeister", because some of that source's slips
are stored mis-encoded and no amount of correct decoding on our side can undo
that.

Both problems are gone by construction now: the phrases are ours, and there is
nothing to decode. What these check is that they stay that way.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from app.services import greeting_phrase
from app.services.greeting_phrase import MAX_LENGTH, PHRASES, get_phrase

_MODULE = Path(greeting_phrase.__file__)


class TestEveryPhraseIsFitToRender:
    """It goes into a heading, under a name, unescaped by the eye that reads it."""

    @pytest.mark.parametrize("phrase", PHRASES)
    def test_it_fits_on_the_line(self, phrase: str) -> None:
        assert 0 < len(phrase) <= MAX_LENGTH, f"{phrase!r} is {len(phrase)} chars"

    @pytest.mark.parametrize("phrase", PHRASES)
    def test_it_is_a_sentence_not_markup(self, phrase: str) -> None:
        assert "<" not in phrase
        assert ">" not in phrase
        assert phrase == " ".join(phrase.split()), "stray or repeated whitespace"
        assert phrase[0].isupper(), "a phrase starts as a sentence does"
        assert phrase[-1] in ".!?", "a phrase ends as a sentence does"

    @pytest.mark.parametrize("phrase", PHRASES)
    def test_it_cannot_arrive_mis_encoded(self, phrase: str) -> None:
        """Plain ASCII, so no byte of it can be mangled in transit or storage.

        The reported "JÃ¤germeister" was a UTF-8 string decoded as Latin-1
        somewhere upstream. Nothing here travels, but keeping the set to ASCII
        means a future editor cannot reintroduce the failure mode by pasting
        text with an umlaut in it.
        """
        assert phrase.isascii(), f"{phrase!r} is not plain ASCII"

    def test_they_are_all_different(self) -> None:
        assert len(set(PHRASES)) == len(PHRASES)


class TestItCostsTheRequestNothing:
    def test_the_module_reaches_nothing(self) -> None:
        """No network, no Redis, no background task - the reason this module
        existed at all was a third-party fetch, and it does not do that now."""
        source = _MODULE.read_text(encoding="utf-8")
        code = source.split('"""', 2)[-1]  # past the module docstring
        for forbidden in ("httpx", "redis", "asyncio", "requests", "urllib"):
            assert forbidden not in code, f"the render path touches {forbidden}"

    def test_it_is_the_same_for_everyone_within_the_hour(self, monkeypatch) -> None:
        monkeypatch.setattr(time, "time", lambda: 1_699_999_200.0)
        first = get_phrase()
        monkeypatch.setattr(time, "time", lambda: 1_699_999_200.0 + 3599)
        assert get_phrase() == first

    def test_it_changes_with_the_hour(self, monkeypatch) -> None:
        seen = set()
        for hour in range(len(PHRASES)):
            monkeypatch.setattr(time, "time", lambda h=hour: 1_699_999_200.0 + h * 3600)
            seen.add(get_phrase())
        assert len(seen) == len(PHRASES), "a full day should not repeat itself"


def test_the_greeting_is_still_there_to_fall_back_to(monkeypatch) -> None:
    """The template shows the greeting word when there is no phrase, and that
    contract has to survive the source changing underneath it."""
    monkeypatch.setattr(greeting_phrase, "PHRASES", ())
    assert get_phrase() is None
