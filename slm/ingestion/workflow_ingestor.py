"""
Workflow Ingestor — captures knowledge from completed workflow runs.

After each workflow run, this module ingests the outputs (discovery_context.json,
quality_pack.json, review_pack.md, etc.) and extracts new domain knowledge
to grow the knowledge base over time.

This is how the SLM learns from experience without fine-tuning.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from slm.core.knowledge_store import KnowledgeStore


class WorkflowIngestor:
    """Ingests completed workflow outputs into the knowledge store."""

    def __init__(self, store: Optional[KnowledgeStore] = None):
        self._store = store or KnowledgeStore()

    def ingest_run(self, story_key: str, runs_dir: str) -> dict:
        """Ingest all outputs from a completed workflow run.

        Args:
            story_key: The Jira story key (e.g., PULSE-3730).
            runs_dir: Path to the runs/<storyKey>/ directory.

        Returns:
            Summary of what was ingested.
        """
        summary = {
            "story_key": story_key,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "entries_added": 0,
            "files_processed": [],
            "errors": [],
        }

        ingestors = [
            ("discovery_context.json", self._ingest_discovery_context),
            ("quality_pack.json", self._ingest_quality_pack),
            ("review_pack.md", self._ingest_review_pack),
            ("publish_report.json", self._ingest_publish_report),
            ("agent_bus.jsonl", self._ingest_agent_bus),
        ]

        for filename, ingest_fn in ingestors:
            filepath = os.path.join(runs_dir, filename)
            if os.path.exists(filepath):
                try:
                    count = ingest_fn(story_key, filepath)
                    summary["entries_added"] += count
                    summary["files_processed"].append(filename)
                except Exception as e:
                    summary["errors"].append(f"{filename}: {str(e)}")
            else:
                summary["errors"].append(f"{filename}: file not found")

        return summary

    def _ingest_discovery_context(self, story_key: str, filepath: str) -> int:
        """Extract knowledge from discovery_context.json."""
        with open(filepath) as f:
            data = json.load(f)

        count = 0
        source = f"workflow:{story_key}/discovery_context.json"

        for rule in data.get("resolvedContext", {}).get("businessRules", []):
            if rule and len(rule.strip()) > 10:
                self._store.add(
                    text=f"[{story_key}] Business rule: {rule}",
                    category="business_rule",
                    source=source,
                    metadata={"story_key": story_key},
                )
                count += 1

        for dep in data.get("resolvedContext", {}).get("dependencies", []):
            if dep and len(dep.strip()) > 5:
                self._store.add(
                    text=f"[{story_key}] Dependency: {dep}",
                    category="domain_rule",
                    source=source,
                    metadata={"story_key": story_key},
                )
                count += 1

        for assumption in data.get("assumptions", []):
            text = assumption.get("text", "") if isinstance(assumption, dict) else str(assumption)
            if text and assumption.get("approved", False):
                self._store.add(
                    text=f"[{story_key}] Approved assumption (now fact): {text}",
                    category="domain_rule",
                    source=source,
                    metadata={"story_key": story_key, "was_assumption": True},
                )
                count += 1

        return count

    def _ingest_quality_pack(self, story_key: str, filepath: str) -> int:
        """Extract test patterns from quality_pack.json."""
        with open(filepath) as f:
            data = json.load(f)

        count = 0
        source = f"workflow:{story_key}/quality_pack.json"

        test_cases = data.get("testCases", [])
        components_seen = set()
        types_seen = set()

        for tc in test_cases:
            component = tc.get("Test Component", "")
            testing_type = tc.get("Testing Type", "")
            if component:
                components_seen.add(component)
            if testing_type:
                types_seen.add(testing_type)

        if components_seen:
            self._store.add(
                text=f"[{story_key}] Coverage components used: {', '.join(sorted(components_seen))}. "
                f"Total test cases: {len(test_cases)}.",
                category="test_pattern",
                source=source,
                metadata={"story_key": story_key, "test_case_count": len(test_cases)},
            )
            count += 1

        review = data.get("reviewSummary", {})
        open_risks = review.get("openRisks", [])
        for risk in open_risks:
            if risk and len(str(risk).strip()) > 10:
                self._store.add(
                    text=f"[{story_key}] Open risk from test review: {risk}",
                    category="test_pattern",
                    source=source,
                    metadata={"story_key": story_key},
                )
                count += 1

        return count

    def _ingest_review_pack(self, story_key: str, filepath: str) -> int:
        """Extract review insights from review_pack.md."""
        with open(filepath) as f:
            content = f.read()

        if len(content.strip()) < 50:
            return 0

        source = f"workflow:{story_key}/review_pack.md"
        self._store.add(
            text=f"[{story_key}] Test review summary: {content[:500]}",
            category="test_pattern",
            source=source,
            metadata={"story_key": story_key},
        )
        return 1

    def _ingest_publish_report(self, story_key: str, filepath: str) -> int:
        """Extract publishing outcomes from publish_report.json."""
        with open(filepath) as f:
            data = json.load(f)

        count = 0
        source = f"workflow:{story_key}/publish_report.json"

        errors = data.get("errors", [])
        for error in errors:
            if error:
                self._store.add(
                    text=f"[{story_key}] Jira publish error: {error}",
                    category="known_limitation",
                    source=source,
                    metadata={"story_key": story_key},
                )
                count += 1

        warnings = data.get("warnings", [])
        for warning in warnings:
            if warning:
                self._store.add(
                    text=f"[{story_key}] Jira publish warning: {warning}",
                    category="known_limitation",
                    source=source,
                    metadata={"story_key": story_key},
                )
                count += 1

        return count

    def _ingest_agent_bus(self, story_key: str, filepath: str) -> int:
        """Extract workflow patterns from agent_bus.jsonl."""
        count = 0
        source = f"workflow:{story_key}/agent_bus.jsonl"
        failures = []

        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("status") == "FAILED":
                        failures.append(entry)
                except json.JSONDecodeError:
                    continue

        for failure in failures:
            block = failure.get("block", "unknown")
            message = failure.get("message", "no details")
            errors = failure.get("errors", [])
            error_text = "; ".join(str(e) for e in errors) if errors else "no error details"

            self._store.add(
                text=f"[{story_key}] Workflow failure in {block} block: {message}. Errors: {error_text}",
                category="known_limitation",
                source=source,
                metadata={"story_key": story_key, "block": block},
            )
            count += 1

        return count
