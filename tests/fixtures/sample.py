"""Small fixture used by function_to_svg tests."""

def normalize(values: list[float]) -> list[float]:
    """Normalize values by their maximum magnitude."""
    peak = max(abs(v) for v in values) or 1.0
    return [v / peak for v in values]


def analyze(values: list[float], threshold: float = 0.5) -> dict:
    """Normalize values and count samples above the threshold."""
    scaled = normalize(values)
    selected = [v for v in scaled if v >= threshold]
    return {"scaled": scaled, "count": len(selected)}
