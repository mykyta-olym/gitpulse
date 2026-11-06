"""CustomCheck.check_code must not shadow a built-in R01-R13 code.

The model carried a ``_validate_check_code`` helper documenting this rule, but it
was a plain ``@staticmethod`` nothing ever called - and the create endpoint passes
the client's ``check_code`` through verbatim. A custom check could therefore be
created as "R05" and shadow the built-in. It is now a SQLAlchemy ``@validates``
hook, so assignment enforces it.
"""

import pytest

from app.models.custom_check import CustomCheck


class TestCustomCheckCodeValidation:
    @pytest.mark.parametrize("code", ["C01", "C99", "c02"])
    def test_custom_codes_accepted(self, code: str) -> None:
        assert CustomCheck(check_code=code).check_code == code

    @pytest.mark.parametrize("code", ["R05", "R01", "r13"])
    def test_builtin_codes_rejected(self, code: str) -> None:
        # Would have silently succeeded before the validator was wired up.
        with pytest.raises(ValueError, match="must start with 'C' prefix"):
            CustomCheck(check_code=code)

    def test_empty_code_allowed(self) -> None:
        # Empty means "auto-assign the next C-code" in the create endpoint.
        assert CustomCheck(check_code="").check_code == ""
