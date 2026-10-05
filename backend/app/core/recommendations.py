"""Single source of truth for health-class recommendation text (ARCHITECTURE.md 4.7).

Not duplicated in the frontend. Both the technician Diagnostic response and the
EV User battery overview read from this module.
"""

RECOMMENDATIONS: dict[str, str] = {
    "GOOD": "No immediate maintenance required. Continue normal operation.",
    "MONITOR": "Battery degradation detected. Schedule an inspection within the next service interval.",
    "CRITICAL": "Battery health is below the safe threshold. Immediate inspection or replacement is recommended.",
}


def get_recommendation(health_class: str) -> str:
    try:
        return RECOMMENDATIONS[health_class]
    except KeyError:
        raise ValueError(f"Unknown health class: {health_class}")
