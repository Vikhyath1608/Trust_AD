"""
LLM-based classifier with Vector DB write-back.

Uses the Hugging Face Inference API (free tier) for product classification.
Supports both old (<0.22) and new (>=0.22) versions of huggingface_hub.

Setup:
    1. Copy .env.example to .env
    2. Set HF_API_TOKEN to your free token from https://huggingface.co/settings/tokens
    3. pip install huggingface_hub --upgrade     (recommended: get latest)
       OR use as-is with older versions (uses text_generation fallback)
"""
import re
import json
import os
from typing import Dict, Optional, Any
from sentence_transformers import SentenceTransformer

from vectorstore.chroma_store import VectorDBStore
from utils.logging import Logger

try:
    import huggingface_hub
    from huggingface_hub import InferenceClient
    # Detect whether chat_completion is available (added in v0.22)
    _HF_VERSION = tuple(int(x) for x in huggingface_hub.__version__.split(".")[:2])
    _HAS_CHAT_COMPLETION = _HF_VERSION >= (0, 22)
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    _HAS_CHAT_COMPLETION = False

_DEFAULT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"


class LLMClassifierWithWriteBack:
    """
    LLM classifier using Hugging Face Inference API (free tier).

    Automatically selects the correct API method based on the installed
    huggingface_hub version:
      - v0.22+  →  client.chat_completion()   (preferred, structured messages)
      - <v0.22  →  client.text_generation()   (legacy, single prompt string)

    To upgrade:  pip install huggingface_hub --upgrade

    Env vars read from .env:
        HF_API_TOKEN  — your HF access token (required)
        HF_MODEL      — model to use (default: Mistral-7B-Instruct-v0.3)
    """

    MAX_TOKENS = 256

    def __init__(
        self,
        vectordb_store: VectorDBStore,
        embedding_model: SentenceTransformer,
        logger: Optional[Logger] = None
    ):
        self.logger = logger or Logger(verbose=False)
        self.vectordb_store = vectordb_store
        self.embedding_model = embedding_model
        self.client: Optional[Any] = None

        self.model = os.environ.get("HF_MODEL", _DEFAULT_MODEL).strip()
        api_token = os.environ.get("HF_API_TOKEN", "").strip()

        if not HF_AVAILABLE:
            self.logger.info(
                "Info: LLM classifier unavailable — run: pip install huggingface_hub"
            )
            return

        if not api_token:
            self.logger.info(
                "Info: LLM classifier unavailable — HF_API_TOKEN not set in .env\n"
                "  Get a free token at: https://huggingface.co/settings/tokens"
            )
            return

        try:
            self.client = InferenceClient(model=self.model, token=api_token)
            mode = "chat_completion" if _HAS_CHAT_COMPLETION else "text_generation"
            self.logger.info(
                f"✓ LLM classifier initialised  "
                f"model={self.model}  "
                f"hf_hub=v{huggingface_hub.__version__}  "
                f"mode={mode}"
            )
        except Exception as e:
            self.logger.warning(f"Could not initialise HF InferenceClient: {e}")

    # ──────────────────────────────────────────────────────────────────────

    def classify(self, query: str, normalized_query: str) -> Optional[Dict[str, Any]]:
        """
        Classify query via HF Inference API and write result to VectorDB.

        Returns dict with: is_product, category, product, brand, model,
                           confidence, written_to_vectordb
        Returns None on any failure.
        """
        if not self.client:
            return None

        try:
            if _HAS_CHAT_COMPLETION:
                text = self._call_chat_completion(query)
            else:
                text = self._call_text_generation(query)

            if not text:
                return None

            result = self._parse_json_response(text)
            if result is None:
                return None

            result.setdefault("is_product", False)

            written = False
            if self.embedding_model and self.vectordb_store:
                written = self._write_to_vectordb(normalized_query, result)
            result["written_to_vectordb"] = written

            return result

        except Exception as e:
            self.logger.warning(f"LLM classification error for '{query}': {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────
    # API call methods — one per SDK generation
    # ──────────────────────────────────────────────────────────────────────

    def _call_chat_completion(self, query: str) -> str:
        """
        Use client.chat_completion() — available in huggingface_hub >= 0.22.
        Structured system + user messages; better JSON compliance.
        """
        response = self.client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a product-search classifier. "
                        "Always respond with ONLY a valid JSON object — "
                        "no markdown, no explanation, nothing else."
                    )
                },
                {"role": "user", "content": self._build_prompt(query)}
            ],
            max_tokens=self.MAX_TOKENS,
            temperature=0.1
        )
        return response.choices[0].message.content or ""

    def _call_text_generation(self, query: str) -> str:
        """
        Use client.text_generation() — works on all huggingface_hub versions.
        Falls back to a single formatted prompt string.
        """
        # Build a self-contained prompt that includes the system instruction
        full_prompt = (
            "[INST] You are a product-search classifier. "
            "Always respond with ONLY a valid JSON object — "
            "no markdown, no explanation, nothing else.\n\n"
            + self._build_prompt(query)
            + " [/INST]"
        )
        return self.client.text_generation(
            full_prompt,
            max_new_tokens=self.MAX_TOKENS,
            temperature=0.1,
            do_sample=True
        )

    # ──────────────────────────────────────────────────────────────────────
    # Prompt & parsing
    # ──────────────────────────────────────────────────────────────────────

    def _build_prompt(self, query: str) -> str:
        return f"""Classify this search query as a product search or not.

Query: "{query}"

Return ONLY this JSON object (no extra text):
{{
  "is_product": true,
  "category": "Electronics",
  "product": "laptop",
  "brand": "ASUS",
  "model": "VivoBook 15",
  "confidence": 0.95
}}

Rules:
- is_product = true  → specific purchasable product or brand
- is_product = false → informational, tutorial, error, or non-commercial query
- category: Electronics, Clothing, Footwear, Appliances, Beauty, Sports, Vehicles, etc.
- product:  generic type (laptop, headphones, shoes, motorcycle, etc.)
- brand:    brand name if present, else ""
- model:    model name/number if present, else ""
- confidence: 0.0–1.0

Examples (true):  "samsung galaxy s24", "nike air max 270", "tvs ronin", "kawasaki ninja zx-10r"
Examples (false): "how to fix python error", "sign in", "vintage poster design"

JSON only:"""

    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            text = text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            match = re.search(r'\{[\s\S]*?\}', text)
            if match:
                text = match.group(0)
            return json.loads(text)
        except Exception as e:
            self.logger.warning(f"JSON parse error: {e} — raw: {text[:200]}")
            return None

    def _write_to_vectordb(self, normalized_query: str, result: Dict[str, Any]) -> bool:
        try:
            emb = self.embedding_model.encode(normalized_query, convert_to_numpy=True)
            return self.vectordb_store.add_entry(
                normalized_query=normalized_query,
                query_embedding=emb,
                classification_result=result
            )
        except Exception as e:
            self.logger.warning(f"VectorDB write-back failed: {e}")
            return False