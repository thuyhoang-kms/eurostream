#!/bin/bash
# Read-only: pipeline and job definitions (metadata) as the assessment service principal.
set -u
P=eurostream-assessor
for id in 812b0c63-02b0-4f84-8179-c4f6b3125a72 bf3085bc-c28d-409f-a189-ead16559c718 2dc5f6f9-0aa9-4f50-9b64-9a74bb323473; do
  echo "## pipeline $id"
  databricks pipelines get $id -p $P -o json 2>&1 | grep -E '"name"|"catalog"|"schema"|"target"|"serverless"|"continuous"|"channel"|"path"|"run_as_user_name"|"creator_user_name"|"health"|"edition"|"development"|Error' | sort -u
done
for id in 409482910379854 95679000754636 703057792978798 405798465675582; do
  echo "## job $id"
  databricks jobs get $id -p $P -o json 2>&1 | grep -E '"name"|"task_key"|"notebook_path"|"pipeline_id"|"quartz_cron_expression"|"timezone_id"|"pause_status"|"user_name"|"service_principal_name"|"depends_on"|"environment_key"|"source"|"python_file"|"sql_task"|"query_id"|Error'
  echo "### last runs"
  databricks jobs list-runs --job-id $id --limit 5 -p $P -o json 2>&1 | grep -E '"result_state"|"start_time"|"life_cycle_state"|Error' | paste -d' ' - - - | head -5
done
