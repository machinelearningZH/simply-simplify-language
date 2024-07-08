from promptflow.core import tool


def get_cefr_level(score: float) -> str:
    """Get CEFR level from understandability score.

    We calculated these ranges by scoring various text samples where we had an approximate idea of their CEFR level.
    Again these ranges are not perfect, but give a good indication of the CEFR level.
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


@tool
def calculate_levels(original_score: float, simplified_score: float) -> dict:
    # CEFR level mapping to numeric values
    cefr_rank = {
        "A1": 0,
        "A2": 1,
        "A2 bis B1": 2,
        "B1": 3,
        "B2": 4,
        "C1": 5,
        "C1 bis C2": 6,
        "C2": 7,
    }

    # Calculate score delta
    score_delta = original_score - simplified_score

    # Get CEFR levels for both scores using the provided function
    original_cefr = get_cefr_level(original_score)
    simplified_cefr = get_cefr_level(simplified_score)

    # Calculate CEFR level delta using the mapping
    # The delta is calculated as simplified - original to reflect the desired positive/negative outcome
    cefr_level_delta = cefr_rank[original_cefr] - cefr_rank[simplified_cefr]

    # Return the results as a dictionary
    return {
        "original_level": original_cefr,
        "simplified_level": simplified_cefr,
        "level_improvement": cefr_level_delta,
    }
