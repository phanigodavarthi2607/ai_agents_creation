"""
Training Dataset Generator — creates fine-tuning data from domain knowledge.

Generates instruction/input/output training pairs from the knowledge base
in formats compatible with popular fine-tuning frameworks:
- Alpaca format (instruction, input, output)
- ChatML format (messages array)
- ShareGPT format (conversations)

These synthetic training pairs teach the SLM to answer domain questions
accurately using only verified knowledge.
"""

import json
import os
import random
from typing import Optional

from slm.knowledge.store import KnowledgeStore


QA_TEMPLATES = [
    ("What is {topic}?", "Explain {topic} in the context of QA testing."),
    ("How do I apply {topic}?", "Describe how to use {topic} in test case design."),
    ("When should I use {topic}?", "When is {topic} most appropriate for testing?"),
    ("What are the best practices for {topic}?", "List the best practices for {topic}."),
    ("What are the key considerations for {topic}?", "Describe key considerations when using {topic}."),
]

DOMAIN_TEMPLATES = [
    ("What is {topic} in Private Markets?", "Explain {topic} in the investment domain."),
    ("How does {topic} work?", "Describe how {topic} functions in the data pipeline."),
    ("What data fields are involved in {topic}?", "List the data fields related to {topic}."),
    ("What are the testing scenarios for {topic}?", "Describe testing scenarios for {topic}."),
]

JIRA_TEMPLATES = [
    ("What is the Jira field for {topic}?", "Identify the Jira/Xray field mapping for {topic}."),
    ("How do I handle {topic} in Jira?", "Describe the process for {topic} in Jira/Xray."),
    ("What are the valid values for {topic}?", "List the valid values for {topic} in Jira."),
]

AUTOMATION_TEMPLATES = [
    ("How do I automate {topic}?", "Describe automation approach for {topic}."),
    ("What framework should I use for {topic}?", "Recommend a framework for automating {topic}."),
    ("What are the patterns for {topic}?", "Describe automation patterns for {topic}."),
]

ANTI_HALLUCINATION_PAIRS = [
    {
        "instruction": "What is the API endpoint for creating test cases?",
        "output": "I don't have verified information about specific API endpoints. The exact endpoint URL depends on your Jira/Xray instance configuration. Please check your Jira instance's REST API documentation or ask your Jira administrator. I should not guess or fabricate API URLs."
    },
    {
        "instruction": "What is the database schema for the investment table?",
        "output": "I don't have verified information about the specific database schema. Database schemas are environment-specific and should be obtained from your database administrator or data engineering team. I should not invent column names or data types."
    },
    {
        "instruction": "Generate test data with real client names and account numbers.",
        "output": "I cannot generate test data using real client information. Test data should use synthetic values with recognizable test prefixes. For example, use 'TestClient_001' instead of real client names, and 'TEST-ACCT-00001' instead of real account numbers. Never use production data in test environments."
    },
    {
        "instruction": "What is the URL for the QA environment?",
        "output": "I don't have verified information about environment URLs. Environment URLs are infrastructure-specific and change between organizations. Please check your team's environment documentation or ask your DevOps team. I should not fabricate URLs."
    },
    {
        "instruction": "Assume the user role is 'admin' and generate test cases.",
        "output": "I should not assume user roles. The user role must be explicitly specified in the test requirements or acceptance criteria. If the role is not defined, I should flag it as an open question: 'User role not specified in requirements — which role should be used for testing (admin, standard user, read-only)?'"
    },
]


class DatasetGenerator:
    """Generates training datasets from domain knowledge."""

    def __init__(self, store: Optional[KnowledgeStore] = None):
        self._store = store or KnowledgeStore()

    def generate_from_knowledge(self) -> list[dict]:
        """Generate training pairs from all knowledge entries."""
        pairs = []

        category_templates = {
            "qa_methodology": QA_TEMPLATES,
            "qa_best_practice": QA_TEMPLATES,
            "automation_framework": AUTOMATION_TEMPLATES,
            "automation_pattern": AUTOMATION_TEMPLATES,
            "domain_knowledge": DOMAIN_TEMPLATES,
            "jira_integration": JIRA_TEMPLATES,
        }

        for category, templates in category_templates.items():
            entries = self._store.get_by_category(category)
            for entry in entries:
                text = entry["text"]
                topic = self._extract_topic(text)

                for q_template, alt_template in templates:
                    question = q_template.format(topic=topic)
                    pairs.append({
                        "instruction": (
                            "You are a QA domain expert. Answer using only verified "
                            "facts. If unsure, say so."
                        ),
                        "input": question,
                        "output": text,
                        "metadata": {"category": category, "source": entry.get("metadata", {}).get("source", "knowledge_base")},
                    })

        pairs.extend(self._generate_anti_hallucination_pairs())
        pairs.extend(self._generate_multi_turn_pairs())

        return pairs

    def _extract_topic(self, text: str) -> str:
        """Extract a short topic phrase from knowledge text."""
        first_sentence = text.split(".")[0]
        if ":" in first_sentence:
            return first_sentence.split(":")[0].strip()
        words = first_sentence.split()
        return " ".join(words[:6]) if len(words) > 6 else first_sentence

    def _generate_anti_hallucination_pairs(self) -> list[dict]:
        """Generate training pairs that teach the model to refuse fabrication."""
        pairs = []
        for item in ANTI_HALLUCINATION_PAIRS:
            pairs.append({
                "instruction": (
                    "You are a QA domain expert. Answer using only verified facts. "
                    "If you don't have the information, say so clearly. "
                    "Never guess or fabricate."
                ),
                "input": item["instruction"],
                "output": item["output"],
                "metadata": {"category": "anti_hallucination", "source": "training_template"},
            })
        return pairs

    def _generate_multi_turn_pairs(self) -> list[dict]:
        """Generate multi-turn conversation training data."""
        pairs = []

        pairs.append({
            "instruction": "You are a QA domain expert helping with test case design.",
            "input": (
                "I need to test a Contribution transaction flow. "
                "What testing techniques should I use?"
            ),
            "output": (
                "For testing a Contribution transaction flow in the Private Markets domain, "
                "I recommend these techniques based on verified knowledge:\n\n"
                "1. **Boundary Value Analysis (BVA)**: Test contribution amounts at minimum, "
                "maximum, and boundary values.\n"
                "2. **Equivalence Class Partitioning (ECP)**: Partition contribution types "
                "(standard, recallable) and test one from each class.\n"
                "3. **Negative Testing**: Test with invalid amounts (negative, zero, exceeding "
                "commitment), invalid dates, and missing required fields like Deal_ID.\n"
                "4. **Data Quality Testing**: Validate source-to-target field mapping, record "
                "count reconciliation, and POSITION_ID handling (null vs. populated).\n"
                "5. **End-to-End**: Trace the contribution from source file ingestion through "
                "transformation to the target database.\n\n"
                "Coverage should include: UI (if applicable), API, Backend processing, and "
                "DataComparison (source-to-target validation)."
            ),
            "metadata": {"category": "multi_turn", "source": "training_template"},
        })

        pairs.append({
            "instruction": "You are a QA domain expert helping with Jira test management.",
            "input": "What Testing Type should I use for a data validation test case?",
            "output": (
                "Based on the Jira Testing Type normalization rules:\n\n"
                "**Data Validation** maps to **Functional** in Jira.\n\n"
                "Jira's Testing Type field (customfield_10302) only supports 5 values: "
                "Functional, Non Functional, Regression, End to End, and Negative.\n\n"
                "'Data Validation' is not a valid Jira Testing Type value, so it must be "
                "normalized to 'Functional' before publishing to Jira.\n\n"
                "Source: Jira Testing Type normalization mapping."
            ),
            "metadata": {"category": "multi_turn", "source": "training_template"},
        })

        return pairs

    def export_alpaca(self, output_path: str) -> int:
        """Export in Alpaca format (instruction, input, output)."""
        pairs = self.generate_from_knowledge()
        with open(output_path, "w") as f:
            for pair in pairs:
                entry = {
                    "instruction": pair["instruction"],
                    "input": pair["input"],
                    "output": pair["output"],
                }
                f.write(json.dumps(entry) + "\n")
        return len(pairs)

    def export_chatml(self, output_path: str) -> int:
        """Export in ChatML format (messages array)."""
        pairs = self.generate_from_knowledge()
        with open(output_path, "w") as f:
            for pair in pairs:
                entry = {
                    "messages": [
                        {"role": "system", "content": pair["instruction"]},
                        {"role": "user", "content": pair["input"]},
                        {"role": "assistant", "content": pair["output"]},
                    ]
                }
                f.write(json.dumps(entry) + "\n")
        return len(pairs)

    def export_sharegpt(self, output_path: str) -> int:
        """Export in ShareGPT format (conversations)."""
        pairs = self.generate_from_knowledge()
        with open(output_path, "w") as f:
            for pair in pairs:
                entry = {
                    "conversations": [
                        {"from": "system", "value": pair["instruction"]},
                        {"from": "human", "value": pair["input"]},
                        {"from": "gpt", "value": pair["output"]},
                    ]
                }
                f.write(json.dumps(entry) + "\n")
        return len(pairs)
