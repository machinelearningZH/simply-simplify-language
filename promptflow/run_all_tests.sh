#!/bin/bash

# Test set data file
data_file=./test_data.jsonl
# Name (folder) of the flow
flow=./flow-simplify-es
# Name (folder) of the eval flow
eval_flow=./eval-simplify
# Name of the LLM tool node inside the flow (see flow.dag.yaml)
llm_node=simplify_es



# Warn and print if there are existing flows
output=$(pf run list | grep -E '"name"[[:space:]]*:')
if [ ! -z "$output" ]; then
  echo "Warning: There are existing flows. Will be overwritten..."
fi


echo "--------------------------------------------------------------------------"
echo "Running 'simplify-es' flows now"
echo "--------------------------------------------------------------------------"
pf run delete -y --name base_run_4o
pf run delete -y --name base_run_35turbo
pf run delete -y --name base_run_4o_short_instructions_condensed
pf run delete -y --name base_run_35turbo_short_instructions_condensed

pf run create \
  --name base_run_4o \
  --flow $flow \
  --data $data_file \
  --connections $llm_node.model=gpt-4o \
  --column-mapping original_text='${data.original_text}' \
  --set display_name='Einfache Sprache: GPT-4o (default)'

pf run create \
  --name base_run_4o_short_instructions_condensed \
  --flow $flow \
  --data $data_file \
  --connections simplify_es.model=gpt-4o \
  --variant '${rules_es.short_instructions}' \
  --variant '${completeness.condensed}' \
  --column-mapping original_text='${data.original_text}' \
  --set display_name='Einfache Sprache: GPT-4o (short instructions, condensed)'

pf run create \
  --name base_run_35turbo \
  --flow $flow \
  --data $data_file \
  --connections simplify_es.model=gpt-3.5-turbo \
  --column-mapping original_text='${data.original_text}' \
  --set display_name='Einfache Sprache: GPT-3.5-turbo (default)'

pf run create \
  --name base_run_35turbo_short_instructions_condensed \
  --flow $flow \
  --data $data_file \
  --connections simplify_es.model=gpt-3.5-turbo \
  --variant '${rules_es.short_instructions}' \
  --variant '${completeness.condensed}' \
  --column-mapping original_text='${data.original_text}' \
  --set display_name='Einfache Sprache: GPT-3.5-turbo (short instructions, condensed)'


echo "--------------------------------------------------------------------------"
echo "Running eval flows now"
echo "--------------------------------------------------------------------------"

# Delete all corresponding eval flows, if any
pf run delete -y --name eval_base_run_4o
pf run delete -y --name eval_base_run_35turbo
pf run delete -y --name eval_base_run_4o_short_instructions_condensed
pf run delete -y --name eval_base_run_35turbo_short_instructions_condensed

pf run create \
  --name eval_base_run_4o \
  --flow $eval_flow \
  --run base_run_4o \
  --column-mapping model='gpt-4o' original_text='${run.inputs.original_text}' simplified_text='${run.outputs.simplified_text}' prompt='${run.outputs.prompt}' \
  --set display_name='Evaluation ES: GPT-4o (default)'

pf run create \
  --name eval_base_run_4o_short_instructions_condensed \
  --flow $eval_flow \
  --run base_run_4o_short_instructions_condensed \
  --column-mapping model='gpt-4o' original_text='${run.inputs.original_text}' simplified_text='${run.outputs.simplified_text}' prompt='${run.outputs.prompt}' \
  --set display_name='Evaluation ES: GPT-4o (short instructions, condensed)'

pf run create \
  --name eval_base_run_35turbo \
  --flow $eval_flow \
  --run base_run_35turbo \
  --column-mapping model='gpt-3.5-turbo' original_text='${run.inputs.original_text}' simplified_text='${run.outputs.simplified_text}' prompt='${run.outputs.prompt}' \
  --set display_name='Evaluation ES: GPT-3.5-turbo (default)'

pf run create \
  --name eval_base_run_35turbo_short_instructions_condensed \
  --flow $eval_flow \
  --run base_run_35turbo_short_instructions_condensed \
  --column-mapping model='gpt-3.5-turbo' original_text='${run.inputs.original_text}' simplified_text='${run.outputs.simplified_text}' prompt='${run.outputs.prompt}' \
  --set display_name='Evaluation ES: GPT-3.5-turbo (short instructions, condensed)'


echo "--------------------------------------------------------------------------"
echo "Showing results now"
echo "--------------------------------------------------------------------------"
#pf run show-details --name eval_base_run_4o
#pf run show-details --name eval_base_run_4o_short_instructions_condensed

echo "Metrics for GPT-4o (default)"
pf run show-metrics --name eval_base_run_4o
echo "Metrics for GPT-4o (short instructions, condensed)"
pf run show-metrics --name eval_base_run_4o_short_instructions_condensed

echo "Metrics for GPT-3.5-turbo (default)"
pf run show-metrics --name eval_base_run_35turbo
echo "Metrics for GPT-3.5-turbo (short instructions, condensed)"
pf run show-metrics --name eval_base_run_35turbo_short_instructions_condensed
