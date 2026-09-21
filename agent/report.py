import json
import os
import re
from datetime import datetime
from html import escape


# ---------------------------------------------------------
# Severity helpers
# ---------------------------------------------------------

SEVERITIES = [
    "Critical",
    "High",
    "Medium",
    "Low"
]


def normalize_severity(value):
    """Convert severity text into a standard value."""

    if not value:
        return "Low"

    value = str(value).strip().lower()

    if value == "critical":
        return "Critical"

    if value == "high":
        return "High"

    if value == "medium":
        return "Medium"

    if value == "low":
        return "Low"

    return "Low"


# ---------------------------------------------------------
# Extract AI findings
# ---------------------------------------------------------

def get_finding_cards(ai_review):
    """
    Convert AI review markdown into structured findings.

    This parser intentionally avoids complex regex patterns
    so that different AI response formats do not break the report.
    """

    if not ai_review:
        return []

    text = str(ai_review).replace("\r\n", "\n")

    lines = text.split("\n")

    findings = []
    current = None

    for raw_line in lines:

        line = raw_line.strip()

        # Detect:
        # Finding 1
        # ### Finding 1
        # ## Finding 1
        # #### Finding 1
        finding_match = re.match(
            r"^#{0,6}\s*Finding\s+\d+",
            line,
            re.IGNORECASE
        )

        if finding_match:

            if current:
                findings.append(current)

            current = {
                "issue": "",
                "severity": "Low",
                "category": "",
                "line": "",
                "explanation": "",
                "suggested_fix": ""
            }

            continue

        if current is None:
            continue

        # Remove markdown bold markers
        clean_line = line.replace("**", "")

        # Field extraction
        if clean_line.lower().startswith("issue:"):
            current["issue"] = clean_line.split(
                ":", 1
            )[1].strip()

        elif clean_line.lower().startswith("severity:"):
            value = clean_line.split(
                ":", 1
            )[1].strip()

            current["severity"] = normalize_severity(
                value
            )

        elif clean_line.lower().startswith("category:"):
            current["category"] = clean_line.split(
                ":", 1
            )[1].strip()

        elif clean_line.lower().startswith("line:"):
            current["line"] = clean_line.split(
                ":", 1
            )[1].strip()

        elif clean_line.lower().startswith("explanation:"):
            current["explanation"] = clean_line.split(
                ":", 1
            )[1].strip()

        elif clean_line.lower().startswith(
            "suggested fix:"
        ):
            current["suggested_fix"] = clean_line.split(
                ":", 1
            )[1].strip()

        # Also support "Fix:"
        elif clean_line.lower().startswith("fix:"):
            current["suggested_fix"] = clean_line.split(
                ":", 1
            )[1].strip()

    # Add last finding
    if current:
        findings.append(current)

    # If AI used a different format and no findings
    # were detected, create one general finding.
    if not findings and text.strip():

        findings.append(
            {
                "issue": "AI Code Review",
                "severity": "Low",
                "category": "Code Review",
                "line": "N/A",
                "explanation": text.strip(),
                "suggested_fix": "Review the AI recommendations above."
            }
        )

    return findings


# ---------------------------------------------------------
# Calculate priority summary
# ---------------------------------------------------------

def calculate_priority_summary(findings):

    summary = {
        "total_findings": len(findings),
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }

    for finding in findings:

        severity = normalize_severity(
            finding.get("severity")
        )

        if severity == "Critical":
            summary["critical"] += 1

        elif severity == "High":
            summary["high"] += 1

        elif severity == "Medium":
            summary["medium"] += 1

        elif severity == "Low":
            summary["low"] += 1

    return summary


# ---------------------------------------------------------
# Create report data
# ---------------------------------------------------------

def create_report(
    file_path,
    static_results,
    ai_review=""
):

    findings = get_finding_cards(
        ai_review
    )

    priority = calculate_priority_summary(
        findings
    )

    report = {

        "timestamp": datetime.now().isoformat(),

        "file": file_path,

        "summary": {
            "total_findings": priority[
                "total_findings"
            ],

            "critical": priority[
                "critical"
            ],

            "high": priority[
                "high"
            ],

            "medium": priority[
                "medium"
            ],

            "low": priority[
                "low"
            ],

            "ruff_findings": len(
                static_results.get(
                    "ruff",
                    []
                )
            ),

            "bandit_findings": len(
                static_results.get(
                    "bandit",
                    []
                )
            )
        },

        "priority_summary": priority,

        "findings": findings,

        "static_analysis": static_results,

        "ai_review": ai_review
    }

    return report


# ---------------------------------------------------------
# Save JSON report
# ---------------------------------------------------------

def save_json_report(
    report,
    output_file
):

    folder = os.path.dirname(
        output_file
    )

    if folder:
        os.makedirs(
            folder,
            exist_ok=True
        )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )


# ---------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------

def finding_card_html(finding):

    severity = normalize_severity(
        finding.get("severity")
    )

    issue = escape(
        str(finding.get("issue", ""))
    )

    category = escape(
        str(finding.get("category", ""))
    )

    line = escape(
        str(finding.get("line", ""))
    )

    explanation = escape(
        str(finding.get("explanation", ""))
    )

    suggested_fix = escape(
        str(finding.get("suggested_fix", ""))
    )

    severity_class = severity.lower()

    return f"""
    <div class="finding-card {severity_class}">

        <div class="finding-header">

            <h3>{issue or "Code Issue"}</h3>

            <span class="severity {severity_class}">
                {severity}
            </span>

        </div>

        <div class="finding-info">

            <p>
                <strong>Category:</strong>
                {category or "N/A"}
            </p>

            <p>
                <strong>Line:</strong>
                {line or "N/A"}
            </p>

        </div>

        <div class="finding-section">

            <h4>Explanation</h4>

            <p>
                {explanation or "No explanation provided."}
            </p>

        </div>

        <div class="finding-section">

            <h4>Suggested Fix</h4>

            <p>
                {suggested_fix or "No suggested fix provided."}
            </p>

        </div>

    </div>
    """


# ---------------------------------------------------------
# Static analysis HTML
# ---------------------------------------------------------

def static_analysis_html(
    static_results
):

    ruff_results = static_results.get(
        "ruff",
        []
    )

    bandit_results = static_results.get(
        "bandit",
        []
    )

    html = ""

    html += """
    <div class="static-section">

        <h2>Ruff Findings</h2>

    """

    if not ruff_results:

        html += """
        <div class="success-box">
            No Ruff findings.
        </div>
        """

    else:

        for item in ruff_results:

            code = escape(
                str(item.get("code", ""))
            )

            message = escape(
                str(item.get("message", ""))
            )

            filename = escape(
                str(
                    item.get(
                        "filename",
                        ""
                    )
                )
            )

            location = item.get(
                "location",
                {}
            )

            row = location.get(
                "row",
                "N/A"
            )

            column = location.get(
                "column",
                "N/A"
            )

            html += f"""
            <div class="static-card">

                <h3>{code}</h3>

                <p>
                    <strong>Message:</strong>
                    {message}
                </p>

                <p>
                    <strong>File:</strong>
                    {filename}
                </p>

                <p>
                    <strong>Location:</strong>
                    Line {row}, Column {column}
                </p>

            </div>
            """

    html += """
    </div>

    <div class="static-section">

        <h2>Bandit Findings</h2>

    """

    if not bandit_results:

        html += """
        <div class="success-box">
            No Bandit findings.
        </div>
        """

    else:

        for item in bandit_results:

            test_id = escape(
                str(
                    item.get(
                        "test_id",
                        ""
                    )
                )
            )

            test_name = escape(
                str(
                    item.get(
                        "test_name",
                        ""
                    )
                )
            )

            issue_text = escape(
                str(
                    item.get(
                        "issue_text",
                        ""
                    )
                )
            )

            severity = escape(
                str(
                    item.get(
                        "issue_severity",
                        ""
                    )
                )
            )

            confidence = escape(
                str(
                    item.get(
                        "issue_confidence",
                        ""
                    )
                )
            )

            line_number = escape(
                str(
                    item.get(
                        "line_number",
                        "N/A"
                    )
                )
            )

            html += f"""
            <div class="static-card bandit-card">

                <h3>
                    {test_id} - {test_name}
                </h3>

                <p>
                    <strong>Issue:</strong>
                    {issue_text}
                </p>

                <p>
                    <strong>Severity:</strong>
                    {severity}
                </p>

                <p>
                    <strong>Confidence:</strong>
                    {confidence}
                </p>

                <p>
                    <strong>Line:</strong>
                    {line_number}
                </p>

            </div>
            """

    html += "</div>"

    return html


# ---------------------------------------------------------
# Save HTML report
# ---------------------------------------------------------

def save_html_report(
    report,
    output_file
):

    folder = os.path.dirname(
        output_file
    )

    if folder:
        os.makedirs(
            folder,
            exist_ok=True
        )

    summary = report.get(
        "summary",
        {}
    )

    findings = report.get(
        "findings",
        []
    )

    file_path = escape(
        str(
            report.get(
                "file",
                ""
            )
        )
    )

    timestamp = escape(
        str(
            report.get(
                "timestamp",
                ""
            )
        )
    )

    ai_review = escape(
        str(
            report.get(
                "ai_review",
                ""
            )
        )
    )

    finding_cards = ""

    for finding in findings:

        finding_cards += finding_card_html(
            finding
        )

    if not finding_cards:

        finding_cards = """
        <div class="success-box">
            No AI findings detected.
        </div>
        """

    static_html = static_analysis_html(
        report.get(
            "static_analysis",
            {}
        )
    )

    html = f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width,
      initial-scale=1.0">

<title>AI Code Review Report</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{

    margin: 0;

    padding: 40px;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background: #f4f6f8;

    color: #222;
}}

.container {{

    max-width: 1500px;

    margin: auto;
}}

h1 {{

    font-size: 42px;

    margin-bottom: 5px;
}}

.subtitle {{

    font-size: 20px;

    color: #666;

    margin-bottom: 30px;
}}

.info-card {{

    background: white;

    padding: 30px;

    border-radius: 16px;

    margin-bottom: 30px;

    box-shadow:
        0 4px 15px
        rgba(0,0,0,0.08);
}}

.dashboard {{

    display: grid;

    grid-template-columns:
        repeat(5, 1fr);

    gap: 20px;

    margin-bottom: 30px;
}}

.metric {{

    background: white;

    padding: 25px;

    border-radius: 16px;

    text-align: center;

    box-shadow:
        0 4px 15px
        rgba(0,0,0,0.08);
}}

.metric h3 {{

    margin: 0;

    font-size: 20px;
}}

.metric p {{

    font-size: 40px;

    font-weight: bold;

    margin: 15px 0 0;
}}

.total {{
    border-top: 6px solid #222;
}}

.critical {{
    border-top: 6px solid #b00020;
}}

.high {{
    border-top: 6px solid #e53935;
}}

.medium {{
    border-top: 6px solid #f0a500;
}}

.low {{
    border-top: 6px solid #42a5c6;
}}

.section {{

    background: white;

    padding: 30px;

    border-radius: 16px;

    margin-bottom: 30px;

    box-shadow:
        0 4px 15px
        rgba(0,0,0,0.08);
}}

.finding-card {{

    background: #fff;

    padding: 25px;

    margin-bottom: 20px;

    border-radius: 14px;

    border-left: 7px solid #888;

    box-shadow:
        0 3px 10px
        rgba(0,0,0,0.08);
}}

.finding-card.critical {{
    border-left-color: #b00020;
}}

.finding-card.high {{
    border-left-color: #e53935;
}}

.finding-card.medium {{
    border-left-color: #f0a500;
}}

.finding-card.low {{
    border-left-color: #42a5c6;
}}

.finding-header {{

    display: flex;

    justify-content:
        space-between;

    align-items: center;

    gap: 20px;
}}

.finding-header h3 {{

    margin: 0;

    font-size: 22px;
}}

.severity {{

    padding: 7px 14px;

    border-radius: 20px;

    font-weight: bold;

    color: white;
}}

.severity.critical {{
    background: #b00020;
}}

.severity.high {{
    background: #e53935;
}}

.severity.medium {{
    background: #f0a500;
}}

.severity.low {{
    background: #42a5c6;
}}

.finding-info {{

    margin-top: 15px;

    padding: 15px;

    background: #f5f5f5;

    border-radius: 8px;
}}

.finding-section {{

    margin-top: 20px;
}}

.finding-section h4 {{

    margin-bottom: 8px;
}}

.static-section {{

    margin-top: 30px;
}}

.static-card {{

    background: #f8f9fa;

    padding: 20px;

    margin-bottom: 15px;

    border-radius: 10px;

    border-left: 5px solid #555;
}}

.bandit-card {{

    border-left-color: #b00020;
}}

.success-box {{

    background: #e8f5e9;

    padding: 20px;

    border-radius: 10px;

    color: #256029;
}}

pre {{

    white-space: pre-wrap;

    word-wrap: break-word;

    background: #f1f3f5;

    padding: 20px;

    border-radius: 10px;

    overflow-x: auto;
}}

@media(max-width: 900px) {{

    .dashboard {{

        grid-template-columns:
            repeat(2, 1fr);
    }}
}}

@media(max-width: 600px) {{

    body {{

        padding: 15px;
    }}

    .dashboard {{

        grid-template-columns: 1fr;
    }}

    .finding-header {{

        flex-direction: column;

        align-items: flex-start;
    }}
}}

</style>

</head>

<body>

<div class="container">

<h1>
    AI Code Review Report
</h1>

<div class="subtitle">
    Automated Python Code Analysis
</div>

<div class="info-card">

    <p>
        <strong>File:</strong>
        {file_path}
    </p>

    <p>
        <strong>Timestamp:</strong>
        {timestamp}
    </p>

</div>


<h2>
    Priority Dashboard
</h2>

<div class="dashboard">

    <div class="metric total">

        <h3>Total Findings</h3>

        <p>
            {summary.get("total_findings", 0)}
        </p>

    </div>


    <div class="metric critical">

        <h3>Critical</h3>

        <p>
            {summary.get("critical", 0)}
        </p>

    </div>


    <div class="metric high">

        <h3>High</h3>

        <p>
            {summary.get("high", 0)}
        </p>

    </div>


    <div class="metric medium">

        <h3>Medium</h3>

        <p>
            {summary.get("medium", 0)}
        </p>

    </div>


    <div class="metric low">

        <h3>Low</h3>

        <p>
            {summary.get("low", 0)}
        </p>

    </div>

</div>


<div class="section">

<h2>
    Static Analysis Summary
</h2>

<p>
    <strong>Ruff Findings:</strong>
    {summary.get("ruff_findings", 0)}
</p>

<p>
    <strong>Bandit Findings:</strong>
    {summary.get("bandit_findings", 0)}
</p>

{static_html}

</div>


<div class="section">

<h2>
    AI Review Findings
</h2>

{finding_cards}

</div>


<div class="section">

<h2>
    Raw AI Review
</h2>

<pre>{ai_review}</pre>

</div>

</div>

</body>

</html>
"""

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)


# ---------------------------------------------------------
# Console summary
# ---------------------------------------------------------

def print_summary(report):

    print("\n")

    print("=" * 60)

    print("CODE REVIEW SUMMARY")

    print("=" * 60)

    summary = report.get(
        "summary",
        {}
    )

    print(
        f"Total findings : "
        f"{summary.get('total_findings', 0)}"
    )

    print(
        f"Critical       : "
        f"{summary.get('critical', 0)}"
    )

    print(
        f"High           : "
        f"{summary.get('high', 0)}"
    )

    print(
        f"Medium         : "
        f"{summary.get('medium', 0)}"
    )

    print(
        f"Low            : "
        f"{summary.get('low', 0)}"
    )

    print(
        f"Ruff findings  : "
        f"{summary.get('ruff_findings', 0)}"
    )

    print(
        f"Bandit findings: "
        f"{summary.get('bandit_findings', 0)}"
    )

    print("=" * 60)