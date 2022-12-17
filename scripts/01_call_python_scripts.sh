#!/bin/sh

echo "downloding localstack dependency"
pip install localstack-client

echo  "starting python script"
python /tmp/scripts/create_and_write_to_queue.py

echo "winding down"

# echo "Fetching the messages from SQS and storing it into the Postgres user_logins table"
# python /Users/priyavarman/Documents/SriBalaji-Assessment/data-engineering-take-home/main.py
