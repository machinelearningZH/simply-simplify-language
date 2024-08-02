from promptflow.core import tool

import numpy as np

import tiktoken

# ## Cost per 1000 INPUT token per model, in US-$
# ## see: https://openai.com/api/pricing/
# input_token_price_1k = {}
# input_token_price_1k["gpt-4-turbo"] = 0.01
# input_token_price_1k["gpt-4"] = 0.03
# input_token_price_1k["gpt-4-32k"] = 0.06
# input_token_price_1k["gpt-4o"] = 0.005
# input_token_price_1k["gpt-3.5-turbo"] = 0.0005


# ## Cost per 1000 OUTPUT token per model, in US-$
# ## see: https://openai.com/api/pricing/
# output_token_price_1k = {}
# output_token_price_1k["gpt-4-turbo"] = 0.03
# output_token_price_1k["gpt-4"] = 0.06
# output_token_price_1k["gpt-4-32k"] = 0.12
# output_token_price_1k["gpt-4o"] = 0.015
# output_token_price_1k["gpt-3.5-turbo"] = 0.0015


def count_tokens(model: str, text: str) -> int:
    ## Use tiktoken for models
    count = len(tiktoken.encoding_for_model(model).encode(text))
    return count


@tool
def estimate_cost(
    model: str,
    original_text: str,
    simplified_text: str,
    prompt_used: str,
    prompt_1k_token_cost: float,
    completion_1k_token_cost: float,
    score_improvement: float,
    level_improvement: int,
) -> dict:

    # num token of original text
    original_token = count_tokens(model, original_text)

    # num token of simplified text
    simplified_token = count_tokens(model, simplified_text)

    # num token of full prompt (contains the original text)
    prompt_token = count_tokens(model, prompt_used)

    # total number of tokens (must be <= max. context sitze of the model)
    total_token = prompt_token + simplified_token

    # Only the prompt template, without the actual original text
    instructions_token = prompt_token - original_token

    instructions_cost = (instructions_token / 1000.0) * prompt_1k_token_cost
    prompt_cost = (prompt_token / 1000.0) * prompt_1k_token_cost
    completion_cost = (simplified_token / 1000.0) * completion_1k_token_cost

    total_cost = prompt_cost + completion_cost

    score_improvement_ratio = round((score_improvement / 20.0) / (total_cost * 1000))
    level_improvement_ratio = round((level_improvement / 7.0) / (total_cost * 1000))

    return {
        "instructions_cost": instructions_cost,
        "prompt_cost": prompt_cost,
        "completion_cost": completion_cost,
        "total_cost": total_cost,
        "score_improvement_ratio": score_improvement_ratio,
        "level_improvement_ratio": level_improvement_ratio,
    }
