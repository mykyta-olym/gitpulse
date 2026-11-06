"""The line under the reader's name on the dashboard.

GitLab writes a fixed tagline there - "Your corner of GitLab". Ours changes
through the day instead, so the heading is not the same sentence every time a
teacher opens the page.

**It used to come from api.adviceslip.com.** That was a mistake in kind, not in
degree: a general life-advice API on a dashboard for assessing student teamwork
produced "You will always regret the round of Jaegermeister" and "Don't drink
bleach", and some of its slips are stored mis-encoded at the source, so a
reader saw "JÃ¤germeister" in a heading. It also put a third-party fetch, a
Redis cache, a refresh lock and a background task behind one short string.

The phrases are ours now: craft aphorisms about writing software, which is what
the page is about. They are sayings rather than attributed quotations, so
nothing here can be misattributed to anyone.

**Never on the request path**, and now trivially so: no network, no Redis, no
task. The phrase is a pure function of the hour, so it is the same for every
reader within that hour - the way GitLab's tagline is the same for everyone -
and it changes twenty-four times a day.

The source strings are English like every other string in the app; the
template passes the phrase through ``t()``, so the Slovak catalogue carries a
translation for each of them and a Slovak reader sees a Slovak line.
"""

from __future__ import annotations

import time

#: The line sits under a name in a heading. Anything longer is not a phrase.
MAX_LENGTH = 90

#: Sayings about the craft, not quotations - so there is no one to misattribute
#: them to. Kept short enough to sit on one line under a name.
PHRASES: tuple[str, ...] = (
    "Make it work, make it right, then make it fast.",
    "The best code is the code you did not have to write.",
    "Deleted code has no bugs.",
    "Weeks of coding can save you hours of planning.",
    "Name it for what it does, not for how it does it.",
    "If it is not tested, assume it is broken.",
    "Measure first. Optimise second. Guess never.",
    "Every dependency is a promise someone else has to keep.",
    "Simple and easy are not the same thing.",
    "Fix the cause, not the symptom.",
    "You cannot fix what you cannot reproduce.",
    "A flaky test is worse than no test at all.",
    "Green tests are a claim, not a proof.",
    "A comment that repeats the code will eventually lie.",
    "Write the log line for whoever is reading it at 3am.",
    "Make the change easy, then make the easy change.",
    "Commit small, commit often, explain why.",
    "The bug is in your code before it is in the compiler.",
    "Read the error message. All of it.",
    "Explain it to the duck before you explain it to a person.",
    "A backup is not a backup until you have restored one.",
    "Prefer boring technology for the parts that must not fail.",
    "Code is read far more often than it is written.",
    "Leave the file better than you found it.",
    "If the review is hard, the change is too big.",
    "Reproduce, then diagnose, then fix, then test.",
    "The second-best time to write the test is now.",
    "Delete the code you are afraid to touch, or learn it.",
    "Configuration is code that nobody reviews.",
    "It works on my machine is not a release note.",
)


def get_phrase() -> str | None:
    """The phrase for this hour, or ``None`` if there are none to give.

    Pure and total: no I/O, no failure modes, nothing to schedule. The caller's
    fallback - the time-of-day greeting - is still there for the empty case,
    which keeps the template's contract exactly as it was.
    """
    if not PHRASES:
        return None
    return PHRASES[int(time.time() // 3600) % len(PHRASES)]
