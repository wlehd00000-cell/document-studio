"""Deterministic cost/risk route; this never changes production-quality obligations."""

PROFILES = ("focused", "standard", "showcase")
RISK_SIGNALS = (
    "external_presentation", "spatial_concept", "live_motion",
    "brand_sensitive", "precision_data",
)
SHOWCASE_SIGNALS = frozenset(("external_presentation", "spatial_concept", "live_motion"))
GLOBAL_CHANGES = frozenset(("fact", "argument", "font", "canvas", "style"))
LOCAL_CHANGES = frozenset(("copy", "asset", "export_fix"))


def classify_profile(workflow: dict, requested: str = "auto") -> dict:
    """Select execution *effort*, never permission to omit quality stages.

    The signal list must be explicitly supported by the current request or page map.
    Legacy workflows with no execution profile classify without mutation.
    """
    if not isinstance(workflow, dict):
        raise ValueError("Workflow must be a mapping")
    if requested not in (*PROFILES, "auto"):
        raise ValueError("Unknown execution profile")
    operation = workflow.get("operation", "full")
    if operation not in ("full", "revision", "conversion", "translation"):
        raise ValueError("Unknown workflow operation")
    signals = workflow.get("risk_signals", [])
    if not isinstance(signals, (tuple, list)) or any(signal not in RISK_SIGNALS for signal in signals):
        raise ValueError("Unknown or malformed risk signals")
    changes = workflow.get("changed_roles", [])
    if not isinstance(changes, (tuple, list)):
        raise ValueError("Malformed changed roles")

    if set(signals) & SHOWCASE_SIGNALS:
        minimum = "showcase"
        reasons = ["RISK_" + signal.upper() for signal in RISK_SIGNALS if signal in signals and signal in SHOWCASE_SIGNALS]
    elif operation == "translation":
        minimum = "focused"
        reasons = ["TRANSLATION"]
    elif operation == "conversion" and workflow.get("reviewed_input"):
        minimum = "focused"
        reasons = ["REVIEWED_CONVERSION"]
    elif operation == "revision" and changes and set(changes) <= LOCAL_CHANGES and workflow.get("pages", "all") != "all":
        minimum = "focused"
        reasons = ["SCOPED_LOCAL_REVISION"]
    else:
        minimum = "standard"
        reasons = ["STANDARD_SCOPE"]
        if operation == "revision" and set(changes) & GLOBAL_CHANGES:
            reasons.append("GLOBAL_OR_SUBSTANTIVE_CHANGE")
        if operation == "conversion" and not workflow.get("reviewed_input"):
            reasons.append("UNREVIEWED_CONVERSION")

    for signal in ("brand_sensitive", "precision_data"):
        if signal in signals:
            reasons.append("QUALITY_" + signal.upper())

    stored = workflow.get("execution_profile", "auto")
    candidate = requested if requested != "auto" else stored
    if candidate not in (*PROFILES, "auto"):
        raise ValueError("Unknown stored execution profile")
    actual = max((minimum, candidate if candidate != "auto" else minimum), key=PROFILES.index)
    if candidate != "auto" and PROFILES.index(candidate) < PROFILES.index(minimum):
        reasons.append("DOWNGRADE_BLOCKED")
    elif actual != minimum:
        reasons.append("USER_UPSHIFT")
    return {"execution_profile": actual, "profile_reason_codes": reasons}
