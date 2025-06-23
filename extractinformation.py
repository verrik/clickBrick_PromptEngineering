# JSON Schema Builder: https://katherlab.github.io/LLMAIx/

"""clickBrick_allprompts.py

CLI utility to batch‑screen German anamnesis reports for depressive symptoms
using an OpenAI‑compatible LLM endpoint.  Designed for reproducibility and for
public release alongside the accompanying medical manuscript (Verhees et al.,
2025, doi: ... ... ...).

Usage
-----
$ python run_depression_analysis.py \
    --input clean_060624_LLM_Anamnese.xlsx \
    --output reasoning_4096tokens_depression.csv

Minimal requirements are listed in *requirements.txt*.

All runtime secrets (API key, endpoint URL) are read from environment
variables or a local *.env* file – **never hard‑code credentials.**

"""
from __future__ import annotations

import argparse
import json
import logging
import os
import time
from pathlib import Path
from typing import List

import openai
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

# ---------------------------------------------------------------------------
# CONSTANTS & METADATA -------------------------------------------------------
# ---------------------------------------------------------------------------

# Target clinical conditions derived from Correl et al. (2024)
CONDITIONS: List[str] = [
    "Abhängigkeit",  # addiction
    "Angst",  # anxiety
    "Depression",  # depression
    "Eigengefährdung",  # self endangerment
    "Fremdaggressivität",  # aggression
    "Kognitive Störung",  # cognitive impairment
    "Manie",  # mania
    "Positivsymptomatik",  # positive symptoms
    "Negativsymptomatik",  # negative symptoms
    "Schlaf",  # sleep
    "Selbstverletzung",  # non‑suicidal self harm
    "Suizidalität",  # suicidality
]

# JSON schema used to coerce the model output into a strict format
SCHEMA_WITH_REASONING = {
    "type": "json_schema",
    "json_schema": {
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "reasoning": {"type": "string", "maxLength": 2048},
                "depression": {"type": "boolean"},
            },
            "required": ["reasoning", "depression"],
        },
    },
}

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS -----------------------------------------------------------
# ---------------------------------------------------------------------------


def configure_openai(api_base: str | None = None, api_key: str | None = None) -> None:
    """Populate the *openai* module with runtime credentials.

    Credentials are pulled from parameters **or** the environment (variables
    ``OPENAI_API_BASE`` and ``OPENAI_API_KEY``).
    """
    openai.api_base = api_base or os.getenv("OPENAI_API_BASE")
    openai.api_key = api_key or os.getenv("OPENAI_API_KEY")

    if not openai.api_base or not openai.api_key:
        raise RuntimeError(
            "OpenAI credentials missing – set OPENAI_API_BASE and OPENAI_API_KEY"
        )


def analyse_report(
    report_text: str,
    model: str,
    schema: dict,
    temperature: float = 0.0,
) -> tuple[str | None, bool | None]:
    """Call the LLM and return *(reasoning, depression_flag)*.

    Returns ``(None, None)`` on error so the caller can decide how to handle
    failures (e.g., leave blanks in the CSV but keep processing the batch).
    """
    prompt = (
        "Zeigt der Patient Symptome einer Depression? "
        "Beantworte die Frage Schritt für Schritt und gib eine abschließende Schlussfolgerung! "
        f"{report_text}"
    )

    messages = [{"role": "user", "content": prompt}]

    try:
        start = time.perf_counter()
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            response_format=schema,
            temperature=temperature,
            max_tokens=4096,
        )
        duration = time.perf_counter() - start
        logging.debug("Model call finished in %.2fs", duration)
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("OpenAI call failed: %s", exc, exc_info=True)
        return None, None

    try:
        data = json.loads(response.choices[0].message["content"])
        return data.get("reasoning"), data.get("depression")
    except (KeyError, json.JSONDecodeError) as exc:  # pragma: no cover
        logging.error("Failed to parse model output: %s", exc, exc_info=True)
        return None, None


def batch_analyse(
    input_path: Path,
    output_path: Path,
    model: str,
    *,
    id_column: str = "id",
    text_column: str = "report",
) -> None:
    """Run the depression screen over *input_path* and persist *output_path*.

    The XLSX file is expected to contain at least two columns: an *identifier*
    (default name ``id``) and the *report text* (default name ``report``).
    """
    df = pd.read_excel(input_path, engine="openpyxl")

    reasonings: List[str | None] = []
    flags: List[bool | None] = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Analysing reports"):
        reasoning, flag = analyse_report(
            str(row[text_column]), model=model, schema=SCHEMA_WITH_REASONING
        )
        reasonings.append(reasoning)
        flags.append(flag)

    df["reasoning"] = reasonings
    df["depression"] = flags

    df.to_csv(output_path, index=False)
    logging.info("Saved results to %s", output_path)

# ---------------------------------------------------------------------------
# ENTRY POINT ----------------------------------------------------------------
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:  # noqa: D401 – imperatives are fine
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the input XLSX file containing anamnesis reports.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination for the CSV results.",
    )
    parser.add_argument(
        "--model",
        default="llama-3.3-70b-instruct-q4km",
        help="Model identifier for the ChatCompletion call.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging verbosity level.",
    )
    return parser.parse_args()



def main() -> None:  # noqa: D401 – imperatives are fine
    """Script entry‑point executed by the CLI."""
    load_dotenv()  # Read .env if present (does nothing otherwise)

    args = parse_args()
    logging.basicConfig(level=args.log_level, format="%(levelname)s: %(message)s")

    configure_openai()  # uses env vars

    batch_analyse(
        input_path=args.input,
        output_path=args.output,
        model=args.model,
    )


if __name__ == "__main__":
    main()
