from typing import List

from promptflow.core import log_metric, tool


@tool
def aggregate(
    scores_original: List[float],
    scores_simplified: List[float],
    estimated_cost: List[float],
    value_for_money: List[float],
):
    """
    This tool aggregates the processed result of all lines and calculate the accuracy. Then log metric for the accuracy.

    :param scores: List of the output of a readability scorer node.
    """

    # Add your aggregation logic here
    # Aggregate the results of all lines and calculate the accuracy
    avg_score_original = sum(scores_original) / len(scores_original)
    avg_score_simplified = sum(scores_simplified) / len(scores_simplified)

    total_estimated_cost = sum(estimated_cost)
    avg_value_for_money = sum(value_for_money) / len(value_for_money)

    # Log metric the aggregate result
    log_metric(key="avg_original", value=avg_score_original)
    log_metric(key="avg_simplified", value=avg_score_simplified)
    log_metric(key="total_estimated_cost", value=total_estimated_cost)
    log_metric(key="avg_value_for_money", value=avg_value_for_money)

    return {
        "avg_score_original": avg_score_original,
        "avg_score_simplified": avg_score_simplified,
        "estimated_cost": total_estimated_cost,
        "value_for_money": avg_value_for_money,
    }
