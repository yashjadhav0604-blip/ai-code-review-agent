import argparse

from agent.analyzer import analyze_code
from agent.reviewer import AIReviewer
from agent.report import (
    create_report,
    save_json_report,
    print_summary
)


def main():

    parser = argparse.ArgumentParser(
        description="AI Python Code Review Agent"
    )

    parser.add_argument(
        "file",
        help="Python file to review"
    )

    args = parser.parse_args()

    file_path = args.file

    print("=" * 60)
    print("AI CODE REVIEW AGENT")
    print("=" * 60)

    print("\n[1] Reading Python code...")

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        code = file.read()

    print("[2] Running static analysis...")

    static_results = analyze_code(
        file_path
    )

    print("[3] Running AI review...")

    reviewer = AIReviewer()

    ai_review = reviewer.review_code(
        code,
        static_results
    )

    print("[4] Creating report...")

    report = create_report(
        file_path,
        static_results,
        ai_review
    )

    output_file = (
        "reports/review_report.json"
    )

    save_json_report(
        report,
        output_file
    )

    print_summary(report)

    print("\nAI REVIEW")
    print("=" * 60)

    print(ai_review)

    print("\nReport saved to:")
    print(output_file)


if __name__ == "__main__":
    main()