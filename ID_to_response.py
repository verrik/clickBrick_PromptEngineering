# always handy when importing packages @UKDD
# set HTTP_PROXY=http://ukd-proxy:80
# set HTTPS_PROXY=http://ukd-proxy:80

import csv
import requests
import pandas as pd
import os
import time
import glob  # For finding files matching a pattern
import re
import logging

# Configure logging to output messages to the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Replace with your API's details
token_url = 'http://g19a012:8000/token'
username = os.getenv('API_USERNAME')
password = os.getenv('API_PASSWORD')

if not username or not password:
    raise ValueError("Missing credentials! Set the API_USERNAME and API_PASSWORD environment variables.")

print(f"Using username: {username}")
# Request token using username and password
data = {
    'grant_type': 'password',
    'username': username,
    'password': password,
    # Include any additional fields required by the API, such as `scope`
    # 'scope': 'read write',  # Example scope, replace with the actual one if needed
}

# Optional headers (if the API requires them)
headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
}

response = requests.post(token_url, data=data, headers=headers)

# Handle response
if response.status_code == 200:
    token = response.json()
    auth_token = f"{token['token_type']} {token['access_token']}"
    print(f"Access Token: {token['access_token']}")
else:
    print(f"Error: {response.status_code} - {response.text}")

# Configuration
api_url = "http://g19a012:8000/api/v1/modeling/user_tasks"
output_prefix = "run3_"  # Prefix for the output files
# load prompt kit
Prompt_sourcefile = "ClickBrick_Prompting_table_v2.csv"
df_sourcefile = pd.read_csv(Prompt_sourcefile)

# Define the output directory
output_folder = "LLM_output_files_run3"
input_folder = "LLM_api_requests_run3"

# Extract condition names (excluding the first column which contains labels like 'Baseline', 'Rolle', etc.)
conditions = df_sourcefile.columns[1:]

# Ensure the output directory exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Function to retrieve LLM-generated content using task ID
def retrieve_content(task_id):
    headers = {
        "accept": "application/json",
        "Authorization": auth_token,
        "Content-Type": "application/json"
    }

    start_time = time.time()
    response = requests.get(api_url, headers=headers)
    elapsed_time = time.time() - start_time
    logging.info(f"Request for task {task_id} took {elapsed_time:.2f} seconds")

    if response.status_code == 200:
        response_json = response.json()
        tasks = response_json.get("tasks", [])

        # none_tasks_count = 0  # Count tasks that are None
        # for task in tasks:
        #     if task is None:
        #         none_tasks_count += 1

        # Log the number of None tasks
        # logging.info(f"Number of tasks with None: {none_tasks_count}")

        # Find the task matching the task_id
        for task in tasks:
            # if task is None:
            #     continue
            if task.get("task_id") == task_id:
                # return task.get("result", {}).get("content", "Error: No content returned")
                result = task.get("result")
                if result is None or not isinstance(result, dict):
                    return "Error: No valid result returned"
                else:
                    return result.get("content", "Error: No content returned")

        return "Error: Task ID not found"
    else:
        return f"Error: {response.status_code} - {response.text}"

def clean_content(content):
    # Sanitize content to avoid breaking CSV structure.
    content = re.sub(r'[\n\r]+', ' ', content)  # Remove line breaks
    content = content.strip()
    # Extract the True/False value using regex
    match = re.search(r':\s*"(true|false)"', content, re.IGNORECASE)
    if match:
        content = match.group(1).lower()  # Update content with the extracted value
        return content
    return "Error: No boolean value found"

def retrieve_and_write_csv():
    input_file_pattern = os.path.join(input_folder, "output_prompt_task_ID_*.csv")
    input_files = glob.glob(input_file_pattern)

    for input_file in input_files:
        print(f"Processing file: {input_file}")

        with open(input_file, "r", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            rows = list(reader)
            original_fieldnames = reader.fieldnames

        task_id_fields = [field for field in original_fieldnames if field.startswith("Prompt") and field.endswith("Task ID")]
        safe_filename = f"{output_prefix}from_{os.path.basename(input_file)}"
        new_content_fields = [f"{field} Content" for field in task_id_fields]
        output_fieldnames = original_fieldnames + new_content_fields
        output_csv_path = os.path.join(output_folder, safe_filename)

        with open(output_csv_path, "w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
            writer.writeheader()

            for row in rows:
                # Ensure we don't accidentally carry over new keys from a previous loop
                row = {key: row[key] for key in original_fieldnames}

                    # Retrieve content from API using Task ID
                for task_id_field in task_id_fields:
                    if task_id_field in row and "Error" not in row[task_id_field]:
                        task_id = row[task_id_field]
                        # time.sleep(5)  # Ensure the task has time to complete
                        content = retrieve_content(task_id)
                        row[f"{task_id_field} Content"] = clean_content(content)
                    else:
                        content = "Task ID missing or invalid"
                        row[f"{task_id_field} Content"] = content
                

                writer.writerow(row)

            print(f"Output with content for prompts saved to {output_csv_path}")

# Run the script
if __name__ == "__main__":
    retrieve_and_write_csv()
    print("Retrieval and writing complete. Updated output files created for each prompt.")


 # cmd_line prompt: (llm4psy) C:\Users\verheesge\llm4psy\API_call_test>python Different_Prompts_Test.py
 # grammar: broken so far \\ fixed 12/24

### updated for automatic and variable number of input files depending of prompt count