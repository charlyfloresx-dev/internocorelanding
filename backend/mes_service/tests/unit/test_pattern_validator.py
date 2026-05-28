"""
UC-MES-PAT: PatternValidatorService — Phase 152 unit tests.

Pure regex validation — no I/O, no mocks needed.
All tests run against PatternValidatorService.validate() directly.
"""
import uuid
import pytest
from mes_app.services.pattern_validator import PatternValidatorService
from mes_app.schemas.scan_pattern import ScanPatternRead


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pattern(regex: str, error_message: str = "Pattern failed", priority: int = 0) -> ScanPatternRead:
    return ScanPatternRead(
        id=uuid.uuid4(),
        item_code="TEST-ITEM",
        pattern_name="TEST",
        regex=regex,
        error_message=error_message,
        priority=priority,
        is_active=True,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_empty_patterns_always_valid():
    """No patterns configured → any scan is valid."""
    svc = PatternValidatorService()
    assert svc.validate("ANYTHING-123", []) is None


def test_matching_pattern_returns_none():
    """Scan input matches regex → None (valid)."""
    svc = PatternValidatorService()
    patterns = [_pattern(r"^[A-Z]+-\d{3}$")]
    assert svc.validate("TURBO-001", patterns) is None


def test_non_matching_pattern_returns_error_message():
    """Scan input does NOT match regex → returns error_message."""
    svc = PatternValidatorService()
    patterns = [_pattern(r"^[A-Z]+-\d{3}:LOT\d{6}$", error_message="Requiere número de lote")]
    assert svc.validate("TURBO-001", patterns) == "Requiere número de lote"


def test_multiple_patterns_all_pass():
    """Multiple patterns, all satisfied → None."""
    svc = PatternValidatorService()
    patterns = [
        _pattern(r"^TURBO-.+$", "Must start with TURBO-", priority=0),
        _pattern(r"^.+:LOT\d+$", "Must include lot", priority=1),
    ]
    assert svc.validate("TURBO-001:LOT202601", patterns) is None


def test_priority_order_first_failure_wins():
    """Two patterns; lower priority fails first → returns that error."""
    svc = PatternValidatorService()
    patterns = [
        _pattern(r"^TURBO-.+$", "Must start TURBO", priority=0),
        _pattern(r"^.+:LOT\d+$", "Must include lot", priority=1),
    ]
    # "OTHER-001" fails priority=0 first
    assert svc.validate("OTHER-001", patterns) == "Must start TURBO"


def test_priority_order_second_failure():
    """First pattern passes, second fails → second error returned."""
    svc = PatternValidatorService()
    patterns = [
        _pattern(r"^TURBO-.+$", "Must start TURBO", priority=0),
        _pattern(r"^.+:LOT\d+$", "Must include lot", priority=1),
    ]
    # "TURBO-001" passes priority=0, fails priority=1
    assert svc.validate("TURBO-001", patterns) == "Must include lot"


def test_unordered_patterns_sorted_by_priority():
    """Patterns passed in reverse order are still evaluated by priority."""
    svc = PatternValidatorService()
    patterns = [
        _pattern(r"^.+:LOT\d+$", "Must include lot", priority=10),
        _pattern(r"^TURBO-.+$", "Must start TURBO", priority=1),
    ]
    # "OTHER-001" should fail priority=1 ("Must start TURBO") first
    assert svc.validate("OTHER-001", patterns) == "Must start TURBO"


def test_case_sensitive_regex():
    """regex is case-sensitive by default (no re.IGNORECASE)."""
    svc = PatternValidatorService()
    patterns = [_pattern(r"^TURBO-\d{3}$")]
    assert svc.validate("turbo-001", patterns) is not None  # lowercase fails


def test_fullmatch_anchors_enforced():
    """Partial match is NOT enough — fullmatch required."""
    svc = PatternValidatorService()
    patterns = [_pattern(r"[A-Z]+-\d{3}")]  # no anchors
    # fullmatch means the entire string must satisfy the pattern
    assert svc.validate("PREFIX-TURBO-001-SUFFIX", patterns) is not None


def test_special_characters_in_scan_input():
    """Scan inputs with colons and hyphens work correctly."""
    svc = PatternValidatorService()
    patterns = [_pattern(r"^[A-Z0-9-]+:[A-Z]{3}\d{6}$")]
    assert svc.validate("ITEM-007:LOT202601", patterns) is None
    assert svc.validate("ITEM-007", patterns) is not None
