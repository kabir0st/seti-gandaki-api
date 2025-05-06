#!/bin/bash

# Wait for Elasticsearch to start up before running the following commands
echo "Waiting for Elasticsearch to start..."
until curl -s -X GET "http://localhost:9200/_cluster/health" > /dev/null; do
  sleep 5
done

# Set the number of replicas to 0 for all indices
curl -X PUT "http://localhost:9200/_settings" -H 'Content-Type: application/json' -d'
{
  "index" : {
    "number_of_replicas" : 0
  }
}
'

echo "Elasticsearch replica configuration updated!"
