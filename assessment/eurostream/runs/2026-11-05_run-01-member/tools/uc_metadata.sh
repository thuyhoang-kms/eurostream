#!/bin/bash
# Read-only Unity Catalog / workspace metadata listing as the assessment service principal.
# GET-only CLI list calls; never reads table rows.
set -u
P=eurostream-assessor
echo "## identity"; databricks current-user me -p $P -o json | grep -E '"displayName"'
echo "## metastore"; databricks metastores summary -p $P -o json 2>&1 | grep -E '"region"|"name"|"cloud"|Error'
for c in workspace sat; do
  echo "## schemas $c"
  for s in $(databricks schemas list $c -p $P -o json 2>&1 | grep '"full_name"' | sed -E 's/.*"full_name": *"([^"]+)".*/\1/'); do
    echo "schema $s"
    case $s in *information_schema) continue;; esac
    databricks tables list ${s%%.*} ${s#*.} -p $P -o json 2>&1 | grep -E '"full_name"|"table_type"|"data_source_format"|Error' | paste -d' ' - - - | sed 's/^/  /'
  done
done
echo "## jobs"; databricks jobs list -p $P -o json 2>&1 | grep -E '"job_id"|"name"|"creator_user_name"|Error'
echo "## pipelines"; databricks pipelines list-pipelines -p $P -o json 2>&1 | grep -E '"pipeline_id"|"name"|"state"|Error'
echo "## warehouses"; databricks warehouses list -p $P -o json 2>&1 | grep -E '"id"|"name"|"state"|Error'
echo "## apps"; databricks apps list -p $P -o json 2>&1 | grep -E '"name"|"url"|Error' | head -20
echo "## volumes workspace"; for s in $(databricks schemas list workspace -p $P -o json 2>&1 | grep '"name"' | sed -E 's/.*"name": *"([^"]+)".*/\1/'); do databricks volumes list workspace $s -p $P -o json 2>&1 | grep -E '"full_name"|Error' ; done
