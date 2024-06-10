
from typing import List

from promptflow.core import log_metric, tool


@tool
def aggregate(scores: List[float]):
    """
    This tool aggregates the processed result of all lines and calculate the accuracy. Then log metric for the accuracy.

    :param scores: List of the output of a readability scorer node.
    """

    # Add your aggregation logic here
    # Aggregate the results of all lines and calculate the accuracy
    avg_score =  sum(scores) / len(scores)

    # Log metric the aggregate result
    log_metric(key="avg", value=avg_score)

    return avg_score
