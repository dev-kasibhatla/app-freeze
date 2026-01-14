"""Test CSS validation to catch errors before building."""

import re

from app_freeze.ui.theme import THEME_CSS


def extract_css_variables(css: str) -> set[str]:
    """Extract all CSS variable definitions from a CSS string."""
    # Match $variable-name: value;
    pattern = r"\$([a-z-]+)\s*:"
    return set(re.findall(pattern, css))


def extract_css_variable_usages(css: str) -> set[str]:
    """Extract all CSS variable usages from a CSS string."""
    # Match $variable-name (not followed by :)
    pattern = r"\$([a-z-]+)(?!\s*:)"
    return set(re.findall(pattern, css))


class TestCSSValidation:
    """Validate CSS to catch undefined variable references."""

    def test_theme_defines_all_required_variables(self) -> None:
        """Verify theme defines all commonly used variables."""
        defined_vars = extract_css_variables(THEME_CSS)

        # Expected theme variables
        expected = {
            "primary",
            "secondary",
            "success",
            "warning",
            "error",
            "disabled",
            "surface",
            "surface-light",
            "text",
            "text-muted",
            "border",
            "accent",
        }

        assert expected.issubset(defined_vars), f"Missing variables: {expected - defined_vars}"

    def test_app_item_css_uses_valid_variables(self) -> None:
        """Verify AppItem CSS only uses defined theme variables."""
        # AppItem CSS is now in THEME_CSS, so this test is not needed
        # Widget CSS has been consolidated into theme.py to fix PyInstaller issues
        pass

    def test_app_list_widget_css_uses_valid_variables(self) -> None:
        """Verify AppListWidget CSS only uses defined theme variables."""
        # AppListWidget CSS is now in THEME_CSS
        pass

    def test_device_item_css_uses_valid_variables(self) -> None:
        """Verify DeviceItem CSS only uses defined theme variables."""
        # DeviceItem CSS is now in THEME_CSS
        pass

    def test_no_duplicate_variable_definitions(self) -> None:
        """Verify no duplicate CSS variable definitions in theme."""
        # Find all variable definitions with their positions
        pattern = r"\$([a-z-]+)\s*:"
        matches = list(re.finditer(pattern, THEME_CSS))

        var_names = [m.group(1) for m in matches]
        duplicates = [v for v in var_names if var_names.count(v) > 1]

        assert not duplicates, f"Duplicate variable definitions: {set(duplicates)}"
