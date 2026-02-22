"""
Battery Test Bench - Condition Evaluator
Version: 2.0.0

Evaluates condition_type/condition_key/condition_value against battery context.
Handles: always, feature_flag, amendment_match, age_threshold, service_type,
custom_expression.

Used by ProcedureResolver to determine which sections/steps apply to a
specific battery based on data-driven rules (zero code changes to add models).
"""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """Evaluates data-driven conditions against a battery context dict."""

    def evaluate(self, condition_type: str, condition_key: Optional[str],
                 condition_value: Optional[str], context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition against the provided context.

        Args:
            condition_type: One of 'always', 'feature_flag', 'amendment_match',
                           'age_threshold', 'service_type', 'custom_expression'
            condition_key: The key to look up in context (e.g., 'has_heating_foil')
            condition_value: Expected value or threshold (e.g., 'true', '6')
            context: Dict with battery/job metadata:
                - feature_flags: dict of boolean flags from battery_profiles
                - amendment: battery amendment string
                - age_months: battery age in months
                - months_since_service: months since last service
                - service_type: current service type string
                - part_number: battery part number

        Returns:
            True if condition is met, False otherwise
        """
        if not condition_type or condition_type == "always":
            return True

        evaluator = getattr(self, f"_eval_{condition_type}", None)
        if not evaluator:
            logger.warning(f"Unknown condition_type: {condition_type}")
            return False

        try:
            return evaluator(condition_key, condition_value, context)
        except Exception as e:
            logger.error(f"Condition evaluation failed: {condition_type}/"
                         f"{condition_key}={condition_value}: {e}")
            return False

    def _eval_feature_flag(self, key: str, value: str,
                           context: Dict[str, Any]) -> bool:
        """Check if a feature flag matches the expected value."""
        flags = context.get("feature_flags", {})
        if isinstance(flags, str):
            flags = json.loads(flags)
        flag_val = flags.get(key)
        if flag_val is None:
            return False
        expected = value.lower() in ("true", "1", "yes") if isinstance(value, str) else bool(value)
        return bool(flag_val) == expected

    def _eval_amendment_match(self, key: str, value: str,
                              context: Dict[str, Any]) -> bool:
        """Check if battery amendment matches a pattern."""
        amendment = context.get("amendment", "")
        if not value:
            return True
        # Support comma-separated list of amendments
        allowed = [v.strip().upper() for v in value.split(",")]
        return amendment.upper() in allowed

    def _eval_age_threshold(self, key: str, value: str,
                            context: Dict[str, Any]) -> bool:
        """
        Check if age-related value exceeds threshold.
        key format: 'months_since_service' or 'age_months'
        value format: 'N' (integer threshold) or reference like 'recondition_threshold'
        """
        # Determine actual context value
        actual = context.get(key, 0)
        if actual is None:
            actual = 0

        # Determine threshold — can be a number or a reference to another context key
        try:
            threshold = int(value)
        except (ValueError, TypeError):
            # It's a reference key — look it up in context
            threshold = context.get(value, 0)
            if threshold is None:
                threshold = 0

        return actual >= threshold

    def _eval_service_type(self, key: str, value: str,
                           context: Dict[str, Any]) -> bool:
        """Check if current service type matches."""
        current = context.get("service_type", "")
        allowed = [v.strip().lower() for v in value.split(",")]
        return current.lower() in allowed

    def _eval_custom_expression(self, key: str, value: str,
                                context: Dict[str, Any]) -> bool:
        """
        Evaluate a simple expression. Supports:
        - 'key > N', 'key < N', 'key >= N', 'key <= N', 'key == value'
        - 'key in [a,b,c]'

        This is intentionally limited (no eval()) for safety.
        """
        if not value:
            return False

        # Parse simple comparison: "field op value"
        for op in (">=", "<=", "!=", "==", ">", "<"):
            if op in value:
                parts = value.split(op, 1)
                if len(parts) == 2:
                    field = parts[0].strip()
                    expected = parts[1].strip()
                    actual = context.get(field)
                    if actual is None:
                        return False
                    try:
                        actual_num = float(actual)
                        expected_num = float(expected)
                        if op == ">=":
                            return actual_num >= expected_num
                        elif op == "<=":
                            return actual_num <= expected_num
                        elif op == ">":
                            return actual_num > expected_num
                        elif op == "<":
                            return actual_num < expected_num
                        elif op == "==":
                            return actual_num == expected_num
                        elif op == "!=":
                            return actual_num != expected_num
                    except (ValueError, TypeError):
                        if op == "==":
                            return str(actual) == expected
                        elif op == "!=":
                            return str(actual) != expected
                        return False

        logger.warning(f"Could not parse custom expression: {value}")
        return False
