
from promptflow.core import tool



@tool
def get_cefr_level(score: float) -> str:
    """Get CEFR level from understandability score.

    We calculated these ranges by scoring various text samples where we had an approximate idea of their CEFR level. Again these ranges are not perfect, but give a good indication of the CEFR level.
    """
    if score >= 18.3:
        return "A1"
    elif score >= 17.7 and score < 18.3:
        return "A2"
    elif score >= 17.5 and score < 17.7:
        return "A2 bis B1"
    elif score >= 15.7 and score < 17.5:
        return "B1"
    elif score >= 13.7 and score < 15.7:
        return "B2"
    elif score >= 12.4 and score < 13.7:
        return "C1"
    elif score >= 12.2 and score < 12.4:
        return "C1 bis C2"
    elif score < 12.2:
        return "C2"
