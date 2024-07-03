# Promptflow

Prompt flow is a suite of development tools designed to streamline the end-to-end development cycle of LLM-based AI applications.
It is **Open Source** (MIT License) and works completely standalone as a **Python library** ([pypi package](https://pypi.org/project/promptflow/)) and tools like the Visual Studio Code Extension.

**Resources**
- [Github repository](https://github.com/microsoft/promptflow)
- [Published docs](https://microsoft.github.io/promptflow/)
- [Project Homepage @ pypi.org](https://pypi.org/project/promptflow/)
- [Visual Studio Code Extension](https://marketplace.visualstudio.com/items?itemName=prompt-flow.prompt-flow)

## Getting Started

**Note**: We recommend using **GitHub Codespaces** with Devcontainers (see `./devcontainer/devcontainer.json`). 
This will setup a defined dev environment with all tools configured for you.

Alternativly, you can follow the instructions of of the [quickstart](https://microsoft.github.io/promptflow/how-to-guides/quick-start.html) to install everything manually.

The following is inspired by the [flow fine tuning tutorial](https://github.com/microsoft/promptflow/blob/main/examples%2Ftutorials%2Fflow-fine-tuning-evaluation%2Fpromptflow-quality-improvement.md?utm_source=pocket_shared)


### Current features
Main current use case is a way to automate quality testing / regression testing of your prompts against quality metrics (like the ZIX score introduced in this project). 

What you can do with it:
- Enables experimentation of different prompt variations: __"Do I get better results (like ZIX score) if I change this prompt / system message ?"__
- Enables variant testing with different parameters (temperature etc) : __"Which parameter variants provide the best scores?"__ 
- Optimize token consumption: __"Will I get (almost) the same results with a shorter system prompt, e.g. using less token?"__ 
- Enables comparison between different LLM model types: __"Does the expensive model give much better results than the cheaper one?"__
- Provides execution profiling and tracing: __"How long does model A take to process a standard text vs. model B?"__
- Supports batch proccesing and (aggregated) metrics calculation: __"What's the average score of flow variant A over my corpus of test data?"__

### Current Limitations
Currently, we only support the **OpenAI** model connections. Pull requests welcome.

### Validate local setup
Verify if promptflow is installed correctly in your local Python environment by running `pf -v`in your terminal:
```bash
> pf -v

{
  "promptflow": "1.11.0",
  "promptflow-azure": "1.11.0",
  "promptflow-core": "1.11.0",
  "promptflow-devkit": "1.11.0",
  "promptflow-tracing": "1.11.0"
}

Executable '/usr/local/bin/python'
Python (Linux) 3.9.19 (main, May 14 2024, 09:07:43) 
[GCC 10.2.1 20210110]
```

## Create Open AI Connections
Promptflow securely stores connection credentials referenced by flows. 
Before running flows for the first time, you need to create a __connection__ called _"openai_connection"_ once. (The connection data is locally stored for subsequent runs).

```bash
# Override keys with --set to avoid yaml file changes. 
# If not givem will run in interactive mode
cd promptflow
pf connection create --file ./openai_connection.yaml --set api_key=<your_api_key>


```

## Test the "Simplify" Flow
- The flow `flow-simplify-es` is used to execute simplifications based on the "Einfache Sprache" rules.
- You can select different variants (e.g. different LLM models and parameters, different system prompts, different instructions etc.).


The output is always a json with the following schema 
```json
{
  "simplified_text": "<the simplified text>",
  "prompt": "<the full, final prompt used - e.g. including system prompt and original text>"
}
```

You can run from the Visual Studio Code extension, or the `pf` CLI tool. The following shows how to do everything from the CLI.


```bash
# Assuming current working dir is ${workspace_root}/promptflow
# List existing runs
pf run list

# Test the "Simplify Einfache Sprache" flow with the default variannts and text input. 
# --ui will open the trace UI in the browser afterwards
pf flow test --flow ./flow-simplify-es --ui
```

The trace UI should look something like this:
<img src="./_imgs/pf_trace_output_1.png"></img>
<img src="./_imgs/pf_trace_output_2.png"></img>

## Create Batch "Simplify" Flow runs, with different models

To overwrite the "model" property of the flow node that calls the LLM, you need to set the `--connections` parameter. The Node name is `simplify_es`.

```bash
# Assume working directory is /promptflow

# Create a batch run against data.jsonl using gpt-4o
pf run create --name base_run_4o --flow ./flow-simplify-es --data ./flow-simplify-es/data.jsonl --connections simplify_es.model=gpt-4o
# Create a batch run against data.jsonl using gpt-3.5-turbo
pf run create --name base_run_35turbo --flow ./flow-simplify-es --data ./flow-simplify-es/data.jsonl --connections simplify_es.model=gpt-3.5-turbo

# List the runs
pf run list

# Shows the run information
pf run show --name base_run_4o
pf run show --name base_run_35turbo

# Shows the run input and output
pf run show-details --name base_run_4o
pf run show-details --name base_run_35turbo

```

__Note__: Run names need to be unique, so if you run these again, choose a different name or delete the runs first: `pf run delete -y --name base_run_4o && pf run delete -y --name base_run_35turbo`  

# Visualize 
```

## Create a "Batch Run" against test data
- You can also execute the flow against a `batch` of input data from `data.jsonl`
https://microsoft.github.io/promptflow/reference/pf-command-reference.html#pf-run-create
 

## Run the Evaluation flow
The Evaluation flow is a special kind of flow that takes the previous output of a flow run (or a batch) and calculates (aggregated) metrics.

Prepare the 
```bash
cd promptflow/eval-simplify-es
pip install -r requirements.txt
python -m spacy download de_core_news_sm
```

## Visualize Results

