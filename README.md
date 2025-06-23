# clickBrick Prompt Engineering: Optimizing Large Language Model Performance in Clinical Psychiatry
**Note: This documentation is currently under construction. Some sections may be updated or changed as development progresses.**

## Introduction

Prompt engineering is a powerful tool to optimize the use of generative AI in clinical settings, not only in psychiatry [1]. While large language models (LLMs) have shown potential across a range of tasks - from data extraction to psychotherapy [2] - their clinical utility hinges on how prompts are designed. Current reporting is often limited to non-clinical applications or vignettes [3, 4]. A structured approach to prompt engineering could enhance LLM performance. Here, we introduce clickBrick, a systematic method to test and refine prompts for extracting psychopathological features from psychiatric records based on our previous work [5], and evaluate their downstream impact on diagnostic prediction. We applied increasingly structured prompts to locally-run LLMs for extracting expert-annotated symptoms from admission notes. Classifiers trained on these outputs aimed to predict discharge diagnoses (ICD-10) in a dataset of 2,520 in-patient cases. Extraction accuracy varied significantly with prompt design (balanced accuracy: 71.45% to 93.59% for best prompts; 50% to 69.82% for worst). Chain-of-Thought prompts outperformed others in 7 out of 12 symptoms, though simpler prompts worked best for suicidality. Diagnostic classifiers trained on best-prompt outputs also showed superior performance for several diagnoses. Prompt engineering - particularly through iterative, structured and subject-matter expert-led design - is critical for unlocking LLMs’ clinical potential. In mental health research and beyond, it offers a scalable path to improve AI interpretability, accuracy, and real-world relevance.

References
[1] Clusmann, J., Kolbinger, F. R., Muti, H. S., Carrero, Z. I., Eckardt, J.-N., Laleh, N. G., Löffler, C. M. L., Schwarzkopf, S.-C., Unger, M., Veldhuizen, G. P., Wagner, S. J., & Kather, J. N. (2023). The future landscape of large language models in medicine. Communications Medicine, 3(1), 141. https://doi.org/10.1038/s43856-023-00370-1

[2] Heinz, M. V., Mackin, D. M., Trudeau, B. M., Bhattacharya, S., Wang, Y., Banta, H. A., Jewett, A. D., Salzhauer, A. J., Griffin, T. Z., & Jacobson, N. C. (2025). Randomized Trial of a Generative AI Chatbot for Mental Health Treatment. NEJM AI. https://doi.org/10.1056/AIoa2400802

[3] Kresevic, S., Giuffrè, M., Ajcevic, M., Accardo, A., Crocè, L. S., & Shung, D. L. (2024). Optimization of hepatological clinical guidelines interpretation by large language models: A retrieval augmented generation-based framework. Npj Digital Medicine, 7(1), 1–9. https://doi.org/10.1038/s41746-024-01091-y

[4] Wang, L., Chen, X., Deng, X., Wen, H., You, M., Liu, W., Li, Q., & Li, J. (2024). Prompt engineering in consistency and reliability with the evidence-based guideline for LLMs. Npj Digital Medicine, 7(1), 1–9. https://doi.org/10.1038/s41746-024-01029-4

[5] Wiest, I. C., Verhees, F. G., Ferber, D., Zhu, J., Bauer, M., Lewitzka, U., Pfennig, A., Mikolas, P., & Kather, J. N. (2024). Detection of suicidality from medical text using privacy-preserving large language models. The British Journal of Psychiatry, 1–6. https://doi.org/10.1192/bjp.2024.134

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
