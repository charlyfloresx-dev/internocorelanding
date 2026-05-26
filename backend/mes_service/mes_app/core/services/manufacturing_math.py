from decimal import Decimal
from typing import Optional


class ManufacturingMath:
    @staticmethod
    def calculate_productive_time(available_mins: float, planned_downtime_mins: float) -> float:
        """Productive Time = available shift minutes minus scheduled breaks/planned downtime."""
        return max(0.0, available_mins - planned_downtime_mins)

    @staticmethod
    def calculate_lmpu(productive_mins: float, operator_count: int, actual_qty: int) -> float:
        """LMPU (Labor Minutes Per Unit) = (productive_mins × operators) / pieces produced."""
        if actual_qty <= 0:
            return 0.0
        return (productive_mins * operator_count) / actual_qty

    @staticmethod
    def calculate_oee(availability: float, efficiency: float, quality: float) -> float:
        """Overall Equipment Effectiveness = Availability × Efficiency × Quality."""
        return availability * efficiency * quality

    @staticmethod
    def calculate_quality(actual_qty: int, scrap_qty: int) -> float:
        """Quality Factor = (Total Produced - Scrap) / Total Produced."""
        if actual_qty <= 0:
            return 1.0
        return max(0.0, (actual_qty - scrap_qty) / actual_qty)

    @staticmethod
    def calculate_tak_time_seconds(
        productive_mins: float,
        actual_qty: int,
        cycle_time_seconds: Optional[int] = None,
    ) -> float:
        """
        TakTime: seconds consumed per unit produced.

        When cycle_time_seconds is available (time-studied value from StandardTime),
        it takes precedence — it reflects the actual machine rhythm.
        Falls back to the formula-derived value when not yet time-studied.
        """
        if cycle_time_seconds is not None and cycle_time_seconds > 0:
            return float(cycle_time_seconds)
        if actual_qty <= 0:
            return 0.0
        return (productive_mins * 60.0) / actual_qty

    @staticmethod
    def calculate_theoretical_capacity(
        cycle_time_seconds: int,
        available_minutes: float,
    ) -> int:
        """
        Theoretical pieces producible in a shift given machine cycle time.

        cycle_time_seconds: machine cycle time per piece (StandardTime.cycle_time_seconds)
        available_minutes: net productive minutes for the shift (after breaks)
        Returns integer pieces — partial pieces are not countable output.
        """
        if cycle_time_seconds <= 0 or available_minutes <= 0:
            return 0
        available_seconds = available_minutes * 60.0
        return int(available_seconds // cycle_time_seconds)

    @staticmethod
    def calculate_improvement_percentage(current_lmpu: float, target_lmpu: float) -> float:
        """
        Compares current LMPU with a historical target.
        Positive = more efficient (lower LMPU). Negative = less efficient.
        """
        if target_lmpu <= 0 or current_lmpu <= 0:
            return 0.0
        return ((target_lmpu - current_lmpu) / target_lmpu) * 100.0
