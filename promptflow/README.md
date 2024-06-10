# Promptflow

Prompt flow is a suite of development tools designed to streamline the end-to-end development cycle of LLM-based AI applications.
It is **Open Source** (MIT License) and works completely standalone as a **Python library** ([pypi package](https://pypi.org/project/promptflow/)) and tools like the Visual Studio Code Extension.

**Resources**
- [Github repository](https://github.com/microsoft/promptflow)
- [Published docs](https://microsoft.github.io/promptflow/)
- [Project Homepage @ pypi.org](https://pypi.org/project/promptflow/)
- [Visual Studio Code Extension](https://marketplace.visualstudio.com/items?itemName=prompt-flow.prompt-flow)

## Getting started

**Note**: We recommend using **GitHub Codespaces** with Devcontainers (see `./devcontainer/devcontainer.json`). 
This will setup a defined dev environment with all tools configured for you.

Alternativly, you can follow the instructions of of the [quickstart](https://microsoft.github.io/promptflow/how-to-guides/quick-start.html) to install everything manually.



## Evaluate quality of your Prompts 
One use case is a way to automate quality testing / regression testing of your prompts against ground truth and (potentially) "hand 

What you can do with it:
- Enables experimentation of different prompt variations: __"Do I get better results (like ZIX score) if I change this prompt / system message ?"__
- Enables variant testing with different parameters (temperature etc) : __"Which parameter variants provide the best scores?"__ 
- Optimize token consumption: __"Will I get (almost) the same results with a shorter system prompt, e.g. using less token?"__ 
- Enables comparison between different LLM model types: __"Does the expensive model give much better results than the cheaper one?"__
- Provides profiling and tracing, regression testing etc: __"How long does model A take to process a standard text vs. model B?"__
- Supports batch procesing and (aggregated) metrics calculation: __"What's the average score of flow variant A over my corpus of test data?"__

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


## Run "Simplify" Flow
- The flow `promptflow/flow-simplify-es` is used to execute simplifications based on the "Einfache Sprache" rules.
- You can select different variants (e.g. different LLM models and parameters, different system prompts, different instructions etc.).
- You can also execute the flow against a `batch` of input data from `data.jsonl`

The output is always a json with `{simplified_text: "...."}`.

## Run the Evaluation flow
The Evaluation flow is a special kind of flow that takes the previous output of a flow run (or a batch) and calculates (aggregated) metrics.

Prepare the 
```bash
cd promptflow/eval-simplify-es
pip install -r requirements.txt
python -m spacy download de_core_news_sm
```

