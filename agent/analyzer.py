import json
import subprocess
import sys


def run_command(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        return result.stdout

    except Exception as e:
        return str(e)


def run_ruff(file_path):
    command = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        file_path,
        "--output-format",
        "json"
    ]

    output = run_command(command)

    try:
        return json.loads(output) if output else []

    except json.JSONDecodeError:
        return []


def run_bandit(file_path):
    command = [
        sys.executable,
        "-m",
        "bandit",
        "-r",
        file_path,
        "-f",
        "json"
    ]

    output = run_command(command)

    try:
        data = json.loads(output)

        return data.get("results", [])

    except json.JSONDecodeError:
        return []


def analyze_code(file_path):

    print("\nRunning Ruff...")

    ruff_results = run_ruff(file_path)

    print("Running Bandit...")

    bandit_results = run_bandit(file_path)

    return {
        "ruff": ruff_results,
        "bandit": bandit_results
    }