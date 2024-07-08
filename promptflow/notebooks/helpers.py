# Helper function to prepare configs for different flow configurations
import json, os, re
from promptflow.client import PFClient
import pandas as pd

# Set the maximum column width to a higher value, e.g., None for no truncation
pd.set_option("display.max_colwidth", None)


def create_flow_config(
    model="gpt-4o",
    variant=None,
    flow_path="../flow-simplify-es",
    data_path="../test_data.jsonl",
):
    variant_str = re.sub(r"[\$\{\}]", "", variant or "default")
    return {
        "model": model,
        "display_name": f"Simplify ES {model} {variant_str}",
        "run_name": f"run_simplify_es_{model}_{variant_str}",
        "flow_path": flow_path,
        "data_path": data_path,
        "variant": variant or None,
        "column_mapping": {"original_text": "${data.original_text}", "model": model},
    }


def execute_run(pf: PFClient, cfg: dict):
    try:
        # Delete the run if it already exists
        pf.runs.delete(name=cfg["run_name"])
    except:
        pass  # ignore

    run_result = pf.run(
        name=cfg["run_name"],
        flow=cfg["flow_path"],
        data=cfg["data_path"],
        column_mapping=cfg["column_mapping"],
        environment_variables={"PF_LOGGING_LEVEL": "CRITICAL"},
        variant=cfg.get("variant", None),
        stream=False
    )

    duration = run_result.properties["system_metrics"]["duration"]
    prompt_tokens = run_result.properties["system_metrics"]["prompt_tokens"]
    completion_tokens = run_result.properties["system_metrics"]["completion_tokens"]

    details = pf.runs.get_details(run_result)
    metrics = pf.runs.get_metrics(run_result)

    result = {
        "run": run_result,
        "model": cfg["model"],
        "run_name": cfg["run_name"],
        "variant": cfg.get("variant", "default"),
        "duration": duration,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "details": details,
        "metrics": metrics,
    }
    return result


def execute_eval_run(pf: PFClient, cfg, run_result, eval_flow_path="../eval-simplify", prompt_token_cost=0.005, completion_token_cost=0.015):
    eval_run_name = f"eval_{cfg['run_name']}"

    try:
        # Delete the eval run if it already exists
        pf.runs.delete(name=eval_run_name)
    except:
        pass  # ignore

    eval_run_result = pf.run(
        name=eval_run_name,
        flow=eval_flow_path,
        data=cfg["data_path"],  # path to the data file
        run=run_result["run"],  # specify base_run as the run you want to evaluate
        environment_variables={"PF_LOGGING_LEVEL": "CRITICAL"},
        column_mapping={
            "model": cfg["model"],
            "original_text": "${run.inputs.original_text}",
            "simplified_text": "${run.outputs.simplified_text}",
            "prompt": "${run.outputs.prompt}",
            "prompt_1k_token_cost": prompt_token_cost,
            "completion_1k_token_cost": completion_token_cost,
        },  
        stream=False,
    )

    details = pf.runs.get_details(eval_run_result, all_results=True)
    metrics = pf.runs.get_metrics(eval_run_result)

    result = {
        "run": eval_run_result,
        "run_name": eval_run_name,
        "details": details,
        "metrics": metrics,
    }
    return result






