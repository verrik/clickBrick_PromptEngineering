# always handy when importing packages @UKDD
# set HTTP_PROXY=http://ukd-proxy:80
# set HTTPS_PROXY=http://ukd-proxy:80
# UNSET before running the script, otherwise it can't find the server: HTTP_PROXY=, HTTPS_PROXY=

import csv
import requests
import pandas as pd
import os
import time
import logging

# Configure logging to output messages to the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Replace with your API's details
token_url = 'http://g19a012:8000/token'
username = os.getenv('API_USERNAME')
password = os.getenv('API_PASSWORD')
grammar_template = r"""root ::= allrecords
allrecords ::= (
  "{"
ws "\"condition\":" ws boolean ","

  ws "}"
  ws
)

ws ::= ([ \t\n])?

boolean ::= "\"" ("true" | "false") "\"" ws

"""

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
api_url = "http://g19a012:8000/api/v1/modeling/process_text_json"
input_file = "clean_060624_LLM_Anamnese.xlsx"  # Path to your input Excel file
output_prefix = "output_prompt_task_ID"  # Prefix for the output files
reports_csv = "reports.csv"  # Intermediate CSV file

# Define the output directory
output_folder = "LLM_api_requests_run2"

# Ensure the output directory exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# load prompt kit
Prompt_sourcefile = "ClickBrick_Prompting_table_v2.csv"
df_sourcefile = pd.read_csv(Prompt_sourcefile)

# Extract condition names (excluding the first column which contains labels like 'Baseline', 'Rolle', etc.)
conditions = df_sourcefile.columns[1:]
# conditions = df_sourcefile.columns[[7, 10, 12]] # to only supplement the existing data with sleep (col8), self injury (11) ans suicidality (13)

# Function to send data to the API
def send_to_api(data, prompt, grammar):
    payload = {
        "text": f"{data} {prompt}",
        # "text": "Übernahme erfolgt nach konsiliarischer Mitbehandlung in der KNA. Dort eingewiesen bei Sturz und generalisiertem Krampfanfall. Patient verlässt unabgesprochen die dortige Behandlung und wird durch die Polizei in seiner Häuslichkeit aufgefunden. Nach erneuter konsiliarischer Sichtung erfolgt die Übernahme zur fortgesetzten Entzugsbehandlung auf die PSY-S1._x000D__x000D_Aktuelle Anamnese:  Die Umstände der Einlieferung in die KNA kann Herr Grellmann nicht wiedergeben. Er gibt an langjährig Alkohol abhängig zu sein und täglich bis zu 3 L Wein zu trinken. Kürzliche habe er seinen Konsum reduziert, aber durch Belastungsfaktoren ( angebliche Epilepsiediagnose durch ambulanten Neurologen, intermittierenden Lebensüberdruss) gestern wieder bis zu 1,5l Wein getrunken zu haben. Hinsichtlich des aktuellen Konsums macht er jedoch gegenüber verschiedenen Behandlern widersprüchliche Aussagen. Mehrfach äußert er Entlasswunsch, da er seine Zwillinge versorgen müsse. Lt Fremdanamnese sei Herr Grellmann jedoch ledig ohne Kinder. Insgesamt wirkt er affektlabil, inhaltliche Denkstörungen im Sinne von Wahrnehmungsstörungen oder wahnhaft-paranoide Erlebnissymptomatik lassen sich nicht explorieren. Zum Übernahmezeitpunkt ergibt sich ein AAT von 2,6 Promille, ein vegetatives Entzugssyndrom wird vorerst nicht beobachtet. Zeigt die beschriebene Person Anzeichen von Suizidlität?",
        "model": "llama3.1_70b_instruct_q4km",
        "grammar": grammar,
        "n_predict": 1024,
        "temperature": 0.1,
        "repeat_penalty": 1
            }
    headers = {
        "accept": "application/json",
        "Authorization": auth_token,
        "Content-Type": "application/json"
    }

    start_time = time.time()
    response = requests.post(api_url, json=payload, headers=headers)
    elapsed_time = time.time() - start_time
    logging.info(f"Request for task {prompt} took {elapsed_time:.2f} seconds")

    if response.status_code == 200:
        response_json = response.json()
        return response_json.get("task_id", "Error: No task ID returned")
    else:
        return f"Error: {response.status_code} - {response.text}"

# Convert Excel to CSV
def convert_excel_to_csv():
    df = pd.read_excel(input_file)
    if "report" not in df.columns:
        raise KeyError("The 'report' column is missing in the Excel file.")
    df.to_csv(reports_csv, index=False)
    print(f"Excel file converted to CSV: {reports_csv}")

# Read CSV, process it line by line for each prompt, and save separate outputs
def process_csv():
    with open(reports_csv, "r") as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)
        original_fieldnames = reader.fieldnames

    for condition in conditions:
        baseline_prompt = df_sourcefile.loc[df_sourcefile['Unnamed: 0'] == 'Baseline', condition].values[0]
        rolle_prompt = df_sourcefile.loc[df_sourcefile['Unnamed: 0'] == 'Rolle', condition].values[0]
        definition_prompt = df_sourcefile.loc[df_sourcefile['Unnamed: 0'] == 'Definition', condition].values[0]
        example_prompt = df_sourcefile.loc[df_sourcefile['Unnamed: 0'] == 'Beispiel Kurz', condition].values[0]
        baseline_scrambled = df_sourcefile.loc[df_sourcefile['Unnamed: 0'] == 'Baseline_Scrambled&Capitalized', condition].values[0]
        rolle_scrambled = df_sourcefile.loc[df_sourcefile['Unnamed: 0'] == 'Rolle_Scrambled&Capitalized', condition].values[0]
        grammar = grammar_template.replace("condition", condition)
        print(f"Generated grammar for condition '{condition}':\n{grammar}\n")

        # Generate prompts
        prompts = [
            f"{baseline_prompt}",
            f"{rolle_prompt} {baseline_prompt}",
            f"{rolle_prompt} {definition_prompt} {baseline_prompt}",
            f"{rolle_prompt} {example_prompt} {baseline_prompt}",
            f"{baseline_scrambled}", 
            f"{rolle_scrambled} {baseline_scrambled}"
        ]

        print(f"Processing condition: {condition}")

        safe_filename = f"{output_prefix}_{condition}.csv"
        output_csv_path = os.path.join(output_folder, safe_filename)
        # output_fieldnames = original_fieldnames + [f"Prompt {idx} Task ID" for idx in range(1, len(prompts) + 1)] change back once we start with all prompts at once
        output_fieldnames = original_fieldnames + [f"Prompt {idx} Task ID" for idx in range(1, len(prompts) + 1)]

        with open(output_csv_path, "w", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
            writer.writeheader()

            for row in rows:
                # Ensure we don't accidentally carry over new keys from a previous loop
                row = {key: row[key] for key in original_fieldnames}

                # Extract the report column and send to API
                report = row["report"]
               
                if report:
                    for idx, prompt in enumerate(prompts, start=1): # (prompts, start=1) change back once we start with all prompts at once
                        prompt_col_name = f"Prompt {idx} Task ID"  # Ensure consistent fieldname
                    
                        print(f"Processing report with {prompt}")
                        task_id = send_to_api(report, prompt, grammar)
                        row[prompt_col_name] = task_id
                else:
                    for idx in range(1, len(prompts) + 1): # change back to 1 later!
                        row[f"Prompt {idx} Task ID"] = "No report found"

                writer.writerow(row)

        print(f"Output for Prompt saved to {output_csv_path}")

# Run the script
if __name__ == "__main__":
    convert_excel_to_csv()
    process_csv()
    print("Processing complete. Separate output files created for each prompt.")


### instead of receiving results, I get a json file with {
 # "task_id": "bceb4fb8-6c08-4529-8163-5e47c15a1c7b",
 # "status": "queued",
 # "model": "llama3.1_70b_instruct_q4km"
 #}
 # I have to write the task_ID to the csv and retrieve the results in the next step.
 # cool! Done 12/16/24, 1419
 # cmd_line prompt: (llm4psy) C:\Users\verheesge\llm4psy\API_call_test>python Different_Prompts_Test.py
 # grammar: broken so far \\ no longer: fixed before christmas with Fabian's help

