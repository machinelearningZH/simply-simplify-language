# Helper function to prepare configs for different flow configurations
import json, os, re
from promptflow.client import PFClient

from IPython.display import JSON, Markdown
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
        environment_variables={"PF_LOGGING_LEVEL": "ERROR"},
        variant=cfg.get("variant", None),
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


def execute_eval_run(
    pf: PFClient, cfg, run_result, eval_flow_path="../eval-simplify"
):
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
        column_mapping={
            "model": cfg["model"],
            "original_text": "${run.inputs.original_text}",
            "simplified_text": "${run.outputs.simplified_text}",
            "prompt": "${run.outputs.prompt}",
        },  # map the url field from the data to the url input of the flow
        stream=True,
    )
    
    details = pf.runs.get_details(eval_run_result)
    metrics = pf.runs.get_metrics(eval_run_result)

    result = {
        "run": eval_run_result,
        "run_name": eval_run_name,
        "details": details,
        "metrics": metrics,
    }
    return result


def result_markdown(result):
    return Markdown(
        f"""##### Results for __\"{result['run_name']}\"__
- __Model__: {result['model']}
- __Variant__: {result['variant']}
- __Duration__: {result['duration']} seconds
- __Prompt tokens__: {result['prompt_tokens']}
- __Completion tokens__: {result['completion_tokens']}
- __Metrics__: {json.dumps(result['metrics'], indent=2)}"""
    )


def compare_simplified(results_list):
    # Initialize an empty DataFrame for the combined results
    combined_df = pd.DataFrame()

    # Loop through each result in the results_list
    for idx, result in enumerate(results_list, start=1):
        # Extract the DataFrame from the result
        df = result["details"]

        # Ensure both required columns are present
        if (
            "inputs.original_text" in df.columns
            and "outputs.simplified_text" in df.columns
        ):
            # Select the required columns
            temp_df = df[["inputs.original_text", "outputs.simplified_text"]].copy()

            # Rename 'outputs.simplified_text' to indicate the source/result
            temp_df.rename(
                columns={"outputs.simplified_text": f'{result["run_name"]}'},
                inplace=True,
            )

            # If it's the first result, initialize combined_df with temp_df
            if combined_df.empty:
                combined_df = temp_df
            else:
                # Merge on 'inputs.original_text' to align simplified texts with their original texts
                combined_df = pd.merge(
                    combined_df, temp_df, on="inputs.original_text", how="outer"
                )

    # Display the combined DataFrame
    return combined_df
