import os
from groq import Groq


class AIReviewer:

    def __init__(self):

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "Groq API key is not configured."
            )

        self.client = Groq(
            api_key=api_key
        )

    def review_code(
        self,
        code,
        static_results
    ):

        prompt = f"""
You are an expert Python code reviewer.

Review the following Python code.

Your task is to identify:

1. Bugs
2. Security vulnerabilities
3. Code quality problems
4. Style problems
5. Performance problems

Static analysis results:

{static_results}

Python code:

{code}

Return the review in the following format:

## CODE REVIEW FINDINGS

### Finding 1
Issue:
Severity:
Category:
Line:
Explanation:
Suggested Fix:

### Finding 2
Issue:
Severity:
Category:
Line:
Explanation:
Suggested Fix:

Use only these severity levels:

Critical
High
Medium
Low

Priority rules:

Critical = severe security vulnerability or serious application failure
High = important security issue or serious bug
Medium = maintainability, correctness, or performance issue
Low = style, cleanup, or minor quality issue

Prioritize security vulnerabilities and serious bugs first.

Do not invent issues that are not supported by the code.

At the end provide:

## SUMMARY

Total Findings:
Critical:
High:
Medium:
Low:

## RECOMMENDED ACTIONS

List the most important fixes in priority order.
"""

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        return response.choices[0].message.content
