class ManufacturingMath:
    @staticmethod
    def calculate_productive_time(available_mins: float, planned_downtime_mins: float) -> float:
        """
        Productive Time excludes scheduled breaks (like lunch) from the total shift time.
        """
        return max(0.0, available_mins - planned_downtime_mins)

    @staticmethod
    def calculate_lmpu(productive_mins: float, operator_count: int, actual_qty: int) -> float:
        """
        LMPU (Labor Minutes Per Unit) 
        Financial metric: Total minutes paid / pieces produced.
        """
        if actual_qty <= 0:
            return 0.0
        return (productive_mins * operator_count) / actual_qty

    @staticmethod
    def calculate_oee(availability: float, efficiency: float, quality: float) -> float:
        """
        Overall Equipment Effectiveness = Availability * Efficiency * Quality
        """
        return availability * efficiency * quality

    @staticmethod
    def calculate_quality(actual_qty: int, scrap_qty: int) -> float:
        """
        Quality Factor: (Total Produced - Scrap) / Total Produced
        """
        if actual_qty <= 0:
            return 1.0 # If nothing produced, we assume 100% quality potential (or 0.0 depending on local policy)
        return max(0.0, (actual_qty - scrap_qty) / actual_qty)

    @staticmethod
    def calculate_tak_time_seconds(productive_mins: float, actual_qty: int) -> float:
        """
        Tak Time: The pulse of the operation. Seconds taken per unit produced.
        """
        if actual_qty <= 0:
            return 0.0
        return (productive_mins * 60.0) / actual_qty

    @staticmethod
    def calculate_improvement_percentage(current_lmpu: float, target_lmpu: float) -> float:
        """
        Compares current LMPU with a historical target.
        Positive value means we are MORE efficient (LMPU is lower).
        Negative value means we are LESS efficient.
        """
        if target_lmpu <= 0 or current_lmpu <= 0:
            return 0.0
        # Improvement = (Target - Current) / Target * 100
        return ((target_lmpu - current_lmpu) / target_lmpu) * 100.0
