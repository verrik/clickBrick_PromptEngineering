# clickBrick Prompt Engineering: Optimizing Large Language Model Performance in Clinical Psychiatry
**Note: This documentation is currently under construction. Some sections may be updated or changed as development progresses.**

## Introduction

[replace with Abstract]

add link to preprint

## General Setup Instructions

Before running the scripts, please ensure the following setup steps are completed:

1. **Python Installation**: Make sure Python is installed on your system. The scripts are compatible with Python 3.12.
2. **Dependency Installation**: Install the required Python packages, e.g. by using the `requirements.txt` file provided:
   ```bash
   pip install -r requirements.txt
   ```

## Data Preparation

Place your dataset files in accessible paths on your system. Load your API credentials for the local LLM server in the environmental variables.
 
## Script-Specific Instructions

### Prompt Noise Injection (`introducenoise.py`)
As part of clickBrick prompt engineering, NIose Is DLlebirÄtley injected (is deliberately injectes) to create some difficult-to-read prompts.
The idea is credited to Hughes and colleagues. (--> https://github.com/jplhughes/bon-jailbreaking)

#### Usage
Run the script from the command line by specifying the path to your ground truth file data, assembled as specified in our pre-print:

```bash
python introducenoise.py
 ```

### Transdiagnostic Domains Extraction Script (`extractinformation.py`)
This Python script extracts and analyzes specific medical features from patient reports using clickBrick prompt engineering.
It runs on llama.cpp. Please set it up according to the respective github repository and start the llama server. (--> https://github.com/ggerganov/llama.cpp/)
Please also see the LLM Information Extraction ppipeline documentation (LLM-AIx) used for this study.  (--> https://github.com/KatherLab/LLMAIx)

#### Usage
Run the script from the command line by specifying the path to your input file data and specify your extraction pattern (e.g. yes|no, reasoning):

```bash
python extractinformation.py
 ```

### Statistical Analysis Script (`statisticalanalysis.py`)
This Python script extracts the desired answer format from the original LLM answers. 

#### Usage
Specify the path to your LLM output file and run the script from the command line. 
    
```bash
python statisticalanalysis.py
 ```

Please contact the corresponding author F. Gerrik Verhees (falkgerrik.verhees@ukdd.de) for any further inquiry.
