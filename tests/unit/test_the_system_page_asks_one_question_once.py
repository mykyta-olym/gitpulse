"""System has four operational cards and shared Pajamas tables.

Domain statistics belong to Users and Courses; user actions belong to Events.
The remaining controls use the same components as the rest of the app.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PAGE = REPO / "src/app/templates/admin_system.html"
HEALTH_PARTIAL = REPO / "src/app/templates/partials/admin/_system_health.html"
MONITORING_PARTIAL = REPO / "src/app/templates/partials/admin/_system_monitoring.html"
JS = REPO / "src/app/templates/static/js/_parts/admin-system"


@pytest.fixture(scope="module")
def src() -> str:
    return PAGE.read_text(encoding="utf-8")


class TestOneCardForOneSubject:
    def test_the_three_configuration_tables_are_one_table(self, src: str) -> None:
        assert "data-tab-panel" not in src, "the configuration tabs are back"
        assert src.count("id='systemConfigTable'") == 1, "there is not exactly one config table"
        for group in ("flags", "llm", "runtime"):
            assert f'data-group="{group}"' in src, f"{group} rows are not in the table"
        assert src.count("{% call data_table(") == 2, (
            "the page draws a table outside Health, Job History and Configuration"
        )
        health_src = HEALTH_PARTIAL.read_text(encoding="utf-8")
        assert health_src.count("{% call data_table(") == 1
        assert "id='healthComponentsTable'" in health_src

    def test_they_are_no_longer_three_headers(self, src: str) -> None:
        """Three card titles for three views of one subject is what was fixed;
        finding them again means the cards came back."""
        for gone in ("LLM Configuration", "Runtime Information"):
            assert gone not in src, f"{gone!r} is a card header again"

    def test_the_page_contains_four_operational_cards_in_order(self, src: str) -> None:
        cards = len(re.findall(r"\{%\s*call card\(", src))
        assert cards == 4
        assert "roleBreakdown" not in src
        assert "chart-4." not in src
        assert (
            src.index("id='systemHealth'")
            < src.index("id='systemMonitoring'")
            < src.index("id='jobQueue'")
            < src.index("id='systemConfiguration'")
        )

    def test_health_and_monitoring_use_shared_stat_cards(self) -> None:
        health_src = HEALTH_PARTIAL.read_text(encoding="utf-8")
        mon_src = MONITORING_PARTIAL.read_text(encoding="utf-8")
        assert "stat_card(" in health_src
        assert "stat_card(" in mon_src
        assert "health-dashboard" not in health_src

    def test_the_switch_between_the_groups(self, src: str) -> None:
        """One entry per group, plus the All the three tabs could not give.

        Drawn as a tab strip: picking one of four views of one table is
        switching, which is what a tab is - the pills this briefly used read as
        filters you turn on and off.
        """
        assert "filter_tabs(" in src
        values = re.findall(r"'value': '(\w+)'", src)
        assert values == ["all", "flags", "llm", "runtime"], values


class TestTheMaintenanceActionsAreThePagesOwn:
    def test_they_sit_in_the_page_header(self, src: str) -> None:
        header = src.split("{% call page_header(", 1)[1].split("{% endcall %}", 1)[0]
        assert "id='btnClearCache'" in header
        assert "id='btnRefreshStats'" not in header

    def test_the_card_that_only_held_them_is_gone(self, src: str) -> None:
        assert "System Actions" not in src, "two buttons have a card around them again"


class TestNothingTheJavascriptReachesForMoved:
    @pytest.mark.parametrize(
        "element_id",
        [
            "queueStatus",
            "jobsTable",
            "btnHealthCheck",
            "systemHealth",
            "btnRefreshMonitoring",
            "systemMonitoringResults",
            "btnClearCache",
            "btnLlmStatus",
            "llmStatusResult",
            "systemConfigTable",
        ],
    )
    def test_the_id_is_still_on_the_page(self, src: str, element_id: str) -> None:
        """admin-system.js reaches for each of these by id. Moving a node from
        one card into a tab panel is safe; losing its id is not."""
        assert f"id='{element_id}'" in src or f'id="{element_id}"' in src, (
            f"#{element_id} disappeared in the restructure"
        )

    def test_the_list_matches_what_the_page_script_actually_asks_for(self) -> None:
        """The list above is only worth having if it keeps up with the script,
        so every id the page's JS looks up has to be accounted for here."""
        wanted: set[str] = set()
        for part in sorted(JS.glob("*.js")):
            wanted |= set(
                re.findall(r"getElementById\('([A-Za-z0-9_]+)'\)", part.read_text(encoding="utf-8"))
            )
        combined = (
            PAGE.read_text(encoding="utf-8")
            + "\n"
            + HEALTH_PARTIAL.read_text(encoding="utf-8")
            + "\n"
            + MONITORING_PARTIAL.read_text(encoding="utf-8")
        )
        missing = {
            found
            for found in wanted
            # An id can reach the markup through a component instead of being
            # written on the element: `select_field('jobTypeFilter')` passes it
            # first, `bulk_action(label, icon, 'btnDeleteSelectedJobs')` third.
            # What matters is that the template names it at all.
            if f"id='{found}'" not in combined
            and f'id="{found}"' not in combined
            and f"'{found}'" not in combined
        }
        assert not missing, (
            f"the page's script looks for ids the page does not have: {sorted(missing)}"
        )
