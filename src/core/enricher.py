"""Main enrichment engine that orchestrates LLM calls for each row."""
import asyncio
from typing import List, Dict, Any, Optional, Callable
from src.llm.client import LLMClient, LLMConfig
from src.prompts import classify, describe, sentiment, extract, custom as custom_prompt
from src.core.batcher import process_batch


class Enricher:
    """Main enrichment engine."""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        self.llm = LLMClient(llm_config)
        self._prompts = {
            "classify": {
                "fn": lambda row, col: classify.classify_prompt(row.get(col, "")),
                "system": classify.CLASSIFY_SYSTEM,
                "new_col": "{col}_category",
            },
            "describe": {
                "fn": lambda row, col: describe.describe_prompt(row.get(col, "")),
                "system": describe.DESCRIBE_SYSTEM,
                "new_col": "{col}_description",
            },
            "sentiment": {
                "fn": lambda row, col: sentiment.sentiment_prompt(row.get(col, "")),
                "system": sentiment.SENTIMENT_SYSTEM,
                "new_col": "{col}_sentiment",
            },
            "extract": {
                "fn": lambda row, col: extract.extract_prompt(row.get(col, "")),
                "system": extract.EXTRACT_SYSTEM,
                "new_col": "{col}_entities",
            },
        }

    def register_custom_prompt(self, template: str, output_column: str = "custom_enrichment"):
        """Register a custom prompt template."""
        def _custom_fn(row, col):
            return custom_prompt.render_custom_prompt(template, row)
        self._prompts["custom"] = {
            "fn": _custom_fn,
            "system": "You are a data enrichment assistant. Follow the user's prompt carefully.",
            "new_col": output_column,
        }

    async def enrich_row(
        self,
        row: Dict[str, Any],
        enrichment_type: str,
        column: str,
        custom_template: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enrich a single row with an LLM call."""
        if enrichment_type not in self._prompts:
            return {**row, "_error": f"Unknown enrichment type: {enrichment_type}"}

        if enrichment_type == "custom" and custom_template:
            self.register_custom_prompt(custom_template)

        prompt_info = self._prompts[enrichment_type]
        prompt = prompt_info["fn"](row, column)
        result = await self.llm.complete(prompt, system_prompt=prompt_info["system"])

        new_col = prompt_info["new_col"].format(col=column)
        return {**row, new_col: result}

    async def enrich_batch(
        self,
        rows: List[Dict[str, Any]],
        enrichment_types: List[str],
        columns: List[str],
        batch_size: int = 10,
        max_concurrency: int = 5,
        show_progress: bool = True,
        custom_template: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Enrich multiple rows with multiple enrichment types."""
        if enrichment_types == ["custom"] and custom_template:
            self.register_custom_prompt(custom_template)

        async def enrich_row_full(row: Dict[str, Any]) -> Dict[str, Any]:
            result_row = dict(row)
            for etype in enrichment_types:
                for col in columns:
                    result_row = await self.enrich_row(
                        result_row, etype, col, custom_template
                    )
            return result_row

        return await process_batch(
            rows, enrich_row_full, batch_size, max_concurrency, show_progress
        )

    def estimate_total_cost(
        self,
        rows: List[Dict[str, Any]],
        enrichment_types: List[str],
        columns: List[str],
    ) -> Dict[str, Any]:
        """Estimate total cost for a job."""
        total_chars = 0
        for row in rows:
            for col in columns:
                val = str(row.get(col, ""))
                total_chars += len(val)
        per_row = self.llm.estimate_cost(total_chars / max(len(rows), 1))
        total = per_row["estimated_cost"] * len(rows) * len(enrichment_types) * len(columns)
        return {
            "rows": len(rows),
            "enrichments": len(enrichment_types) * len(columns),
            "estimated_cost_per_row": per_row["estimated_cost"],
            "estimated_total_cost": round(total, 6),
            "estimated_input_tokens": int(per_row["estimated_input_tokens"] * len(rows) * len(enrichment_types) * len(columns)),
            "estimated_output_tokens": int(per_row["estimated_output_tokens"] * len(rows) * len(enrichment_types) * len(columns)),
        }
