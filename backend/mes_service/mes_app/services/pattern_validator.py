import re
from typing import List, Optional
from mes_app.schemas.scan_pattern import ScanPatternRead


class PatternValidatorService:
    """
    Validates a scan input string against a list of per-item regex patterns.
    Pure function — no I/O. Patterns evaluated in ascending priority order.
    """

    def validate(self, scan_input: str, patterns: List[ScanPatternRead]) -> Optional[str]:
        """
        Returns None if scan_input satisfies all active patterns,
        or the error_message of the first failing pattern.
        """
        for pattern in sorted(patterns, key=lambda p: p.priority):
            if not re.fullmatch(pattern.regex, scan_input):
                return pattern.error_message
        return None
