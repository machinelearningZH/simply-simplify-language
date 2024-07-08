from typing import List
import numpy as np

from promptflow.core import log_metric, tool


@tool
def aggregate(
    original_scores: List[float],
    simplified_scores: List[float],
    scores_improvements: List[float],
    original_levels: List[str],
    simplified_levels: List[str],
    levels_improvements: List[int],
    total_costs: List[float],
    score_improvement_ratios: List[float],
    level_improvement_ratios: List[float],
    
):

    # Average and median scores
    avg_scores_original = np.average (original_scores)
    avg_scores_simplified = np.average (simplified_scores)
    median_scores_simplified = np.median(simplified_scores)
    max_scores_simplified = max(simplified_scores)
    min_scores_simplified = min(simplified_scores)

    # Score improvements
    avg_scores_improvements = np.average(scores_improvements)
    median_scores_improvements = np.median(scores_improvements)
    max_scores_improvements = max(scores_improvements)
    min_scores_improvements = min(scores_improvements)

    # Average and median level improvements
    avg_levels_improvements = np.average(levels_improvements)
    median_levels_improvements = np.median(levels_improvements)
    max_levels_improvements = max(levels_improvements)
    min_levels_improvements = min(levels_improvements)
    
    
    
    # Sum of total cost
    sum_total_cost = sum(total_costs)

      # Log metric the aggregate result
    log_metric(key="avg_score_original", value=avg_scores_original)
    log_metric(key="avg_score_simplified", value=avg_scores_simplified)
    log_metric(key="median_score_simplified", value=median_scores_simplified)
    log_metric(key="max_score_simplified", value=max_scores_simplified)
    log_metric(key="min_score_simplified", value=min_scores_simplified)
    
    log_metric(key="avg_score_improvement", value=avg_scores_improvements)
    log_metric(key="median_score_improvement", value=median_scores_improvements)
    log_metric(key="max_score_improvement", value=max_scores_improvements)
    log_metric(key="min_score_improvement", value=min_scores_improvements)
    
    log_metric(key="sum_total_cost", value=sum_total_cost)

    return {
        "avg_score_original": avg_scores_original,
        "avg_score_simplified": avg_scores_simplified,
        "median_score_simplified": median_scores_simplified,
        "max_score_simplified": max_scores_simplified,
        "min_score_simplified": min_scores_simplified,
        "avg_score_improvement": avg_scores_improvements,
        "median_score_improvement": median_scores_improvements,
        "max_score_improvement": max_scores_improvements,
        "min_score_improvement": min_scores_improvements,
        "sum_total_cost": sum_total_cost,
    }
