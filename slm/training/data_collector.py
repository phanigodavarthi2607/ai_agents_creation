"""
Training Data Collector — accumulates question-answer pairs for future SLM fine-tuning.

Every time an agent queries the knowledge layer and the user approves or
corrects the result, this collector captures the interaction as a training
example. When enough examples accumulate (500+), they can be used to
fine-tune a small language model (Phi-3, Mistral 7B, Llama 3 8B).
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional


TRAINING_DIR = os.environ.get(
    "SLM_TRAINING_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base", "training_data"),
)


class TrainingDataCollector:
    """Collects and manages training examples for future fine-tuning."""

    def __init__(self, training_dir: Optional[str] = None):
        self._dir = training_dir or TRAINING_DIR
        os.makedirs(self._dir, exist_ok=True)
        self._examples_file = os.path.join(self._dir, "examples.jsonl")
        self._stats_file = os.path.join(self._dir, "stats.json")

    def record_example(
        self,
        question: str,
        answer: str,
        category: str,
        source: str,
        agent_name: str,
        story_key: Optional[str] = None,
        user_approved: bool = False,
        user_correction: Optional[str] = None,
    ) -> None:
        """Record a training example from an agent interaction.

        Args:
            question: The question the agent asked.
            answer: The answer returned by the knowledge layer.
            category: Knowledge category.
            source: Source of the answer.
            agent_name: Which agent generated this interaction.
            story_key: Optional Jira story context.
            user_approved: Whether the user approved this answer.
            user_correction: If the user corrected the answer, the corrected version.
        """
        example = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": question,
            "answer": answer,
            "corrected_answer": user_correction,
            "category": category,
            "source": source,
            "agent_name": agent_name,
            "story_key": story_key,
            "user_approved": user_approved,
            "quality": self._assess_quality(user_approved, user_correction),
        }

        with open(self._examples_file, "a") as f:
            f.write(json.dumps(example) + "\n")

        self._update_stats()

    def _assess_quality(self, approved: bool, correction: Optional[str]) -> str:
        """Classify example quality for training prioritization."""
        if approved and not correction:
            return "high"
        if correction:
            return "corrected"
        return "unverified"

    def _update_stats(self) -> None:
        """Update training data statistics."""
        stats = {"total": 0, "high": 0, "corrected": 0, "unverified": 0}

        if os.path.exists(self._examples_file):
            with open(self._examples_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ex = json.loads(line)
                        stats["total"] += 1
                        quality = ex.get("quality", "unverified")
                        if quality in stats:
                            stats[quality] += 1
                    except json.JSONDecodeError:
                        continue

        stats["ready_for_finetuning"] = stats["total"] >= 500
        stats["last_updated"] = datetime.now(timezone.utc).isoformat()

        with open(self._stats_file, "w") as f:
            json.dump(stats, f, indent=2)

    def get_stats(self) -> dict:
        """Get current training data statistics."""
        if os.path.exists(self._stats_file):
            with open(self._stats_file) as f:
                return json.load(f)
        return {"total": 0, "ready_for_finetuning": False}

    def export_for_finetuning(self, output_path: str, min_quality: str = "unverified") -> int:
        """Export training examples in a format suitable for fine-tuning.

        Exports as JSONL with instruction/input/output format compatible
        with common fine-tuning frameworks (Axolotl, Unsloth, etc.).

        Args:
            output_path: Where to write the exported file.
            min_quality: Minimum quality level to include
                         ("high", "corrected", "unverified").

        Returns:
            Number of examples exported.
        """
        quality_order = {"high": 3, "corrected": 2, "unverified": 1}
        min_level = quality_order.get(min_quality, 1)
        count = 0

        with open(output_path, "w") as out:
            if not os.path.exists(self._examples_file):
                return 0

            with open(self._examples_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ex = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    ex_level = quality_order.get(ex.get("quality", "unverified"), 1)
                    if ex_level < min_level:
                        continue

                    final_answer = ex.get("corrected_answer") or ex.get("answer", "")
                    training_entry = {
                        "instruction": (
                            "You are a QA domain expert for the PULSE project. "
                            "Answer the following question using only verified facts "
                            "from the knowledge base. If unsure, say so."
                        ),
                        "input": ex["question"],
                        "output": final_answer,
                        "metadata": {
                            "category": ex.get("category"),
                            "source": ex.get("source"),
                            "agent": ex.get("agent_name"),
                        },
                    }
                    out.write(json.dumps(training_entry) + "\n")
                    count += 1

        return count
