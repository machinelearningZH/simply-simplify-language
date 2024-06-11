from promptflow.core import tool

import numpy as np

import tiktoken

## Cost per 1000 INPUT token per model, in US-$
## see: https://openai.com/api/pricing/
input_token_price_1k = {}
input_token_price_1k["gpt-4-turbo"] = 0.01
input_token_price_1k["gpt-4"] = 0.03
input_token_price_1k["gpt-4-32k"] = 0.06
input_token_price_1k["gpt-4o"] = 0.005
input_token_price_1k["gpt-3.5-turbo"] = 0.0005


## Cost per 1000 OUTPUT token per model, in US-$
## see: https://openai.com/api/pricing/
output_token_price_1k = {}
output_token_price_1k["gpt-4-turbo"] = 0.03
output_token_price_1k["gpt-4"] = 0.06
output_token_price_1k["gpt-4-32k"] = 0.12
output_token_price_1k["gpt-4o"] = 0.015
output_token_price_1k["gpt-3.5-turbo"] = 0.0015


def count_tokens(model: str, text: str) -> int:
    ## TODO use tiktoken
    count = len(tiktoken.encoding_for_model(model).encode(text))
    return count


@tool
def estimate_cost(
    original: str,
    simplified: str,
    model: str,
    prompt_used: str,
    score_original: float,
    score_simplified: float,
) -> str:
    estimated_cost = 0
    value_for_money = 0

    input_tokens_used = count_tokens(model, prompt_used) + count_tokens(model, original)
    output_tokens_used = count_tokens(model, simplified)

    estimated_cost = (input_tokens_used / 1000.0) * input_token_price_1k[model] + (
        output_tokens_used / 1000.0
    ) * output_token_price_1k[model]

    ## TODO adjust the formula to your needs.
    score_improvement = score_simplified - score_original
    # score_improvement_adjusted = np.sign(score_improvement) * logistic(abs(score_improvement), 10, 0.5, 20)
    value_for_money = score_improvement / estimated_cost if estimated_cost != 0 else 0

    return {"cost": estimated_cost, "value": value_for_money}
