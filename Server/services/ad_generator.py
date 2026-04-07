"""
Ad Generator Service.

Uses the Hugging Face Inference API (same model as Client classifier)
to auto-generate a targeting category and keywords from ad creative fields.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from core.config import get_settings
from utils.logging import get_logger

logger = get_logger(__name__)

try:
    import huggingface_hub
    from huggingface_hub import InferenceClient
    _HF_VERSION = tuple(int(x) for x in huggingface_hub.__version__.split(".")[:2])
    _HAS_CHAT_COMPLETION = _HF_VERSION >= (0, 22)
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    _HAS_CHAT_COMPLETION = False

_DEFAULT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
_MAX_TOKENS = 512


class AdGeneratorService:
    """
    Calls the HF Inference API to generate category + keywords for a new ad.

    Reads HF_API_TOKEN and HF_MODEL from environment (same vars as Client).
    """

    def __init__(self) -> None:
        self.client: Optional[Any] = None
        settings = get_settings()
        self.model = (settings.HF_MODEL or os.environ.get("HF_MODEL", _DEFAULT_MODEL)).strip()
        api_token = (settings.HF_API_TOKEN or os.environ.get("HF_API_TOKEN", "")).strip()

        if not HF_AVAILABLE:
            logger.warning("huggingface_hub not installed — ad generation unavailable")
            return

        if not api_token:
            logger.warning("HF_API_TOKEN not set — ad generation unavailable")
            return

        try:
            self.client = InferenceClient(model=self.model, token=api_token)
            mode = "chat_completion" if _HAS_CHAT_COMPLETION else "text_generation"
            logger.info(
                f"AdGeneratorService ready  model={self.model}  mode={mode}"
            )
        except Exception as exc:
            logger.warning(f"Could not init HF InferenceClient: {exc}")

    # ──────────────────────────────────────────────────────────────────────

    def generate(
        self,
        title: str,
        description: str,
        brand: Optional[str] = None,
        destination_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a category string and up to 15 targeting keywords.

        Returns:
            {
                "category":  "Electronics",
                "keywords":  ["laptop", "gaming", "asus", ...],
                "confidence": 0.95,
                "llm_used":  True
            }
        Falls back to a simple heuristic if LLM is unavailable.
        """
        if not self.client:
            return self._heuristic_fallback(title, description, brand)

        try:
            prompt = self._build_prompt(title, description, brand, destination_url)

            if _HAS_CHAT_COMPLETION:
                response = self.client.chat_completion(
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert digital advertising strategist. "
                                "Always respond with ONLY a valid JSON object — "
                                "no markdown, no explanation, nothing else."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=_MAX_TOKENS,
                    temperature=0.15,
                )
                raw = response.choices[0].message.content or ""
            else:
                full_prompt = (
                    "[INST] You are an expert digital advertising strategist. "
                    "Always respond with ONLY a valid JSON object — "
                    "no markdown, no explanation, nothing else.\n\n"
                    + prompt
                    + " [/INST]"
                )
                raw = self.client.text_generation(
                    full_prompt,
                    max_new_tokens=_MAX_TOKENS,
                    temperature=0.15,
                    do_sample=True,
                )

            result = self._parse(raw)
            if result:
                result["llm_used"] = True
                return result

        except Exception as exc:
            logger.warning(f"LLM generation error: {exc}")

        return self._heuristic_fallback(title, description, brand)

    # ──────────────────────────────────────────────────────────────────────
    # Prompt
    # ──────────────────────────────────────────────────────────────────────

    def _build_prompt(
        self,
        title: str,
        description: str,
        brand: Optional[str],
        destination_url: Optional[str],
    ) -> str:
        brand_line = f'Brand: "{brand}"' if brand else ""
        url_line = f'Landing URL: "{destination_url}"' if destination_url else ""
        extra = "\n".join(filter(None, [brand_line, url_line]))

        return f"""You are categorising a digital advertisement for a targeting system.

Ad Title: "{title}"
Ad Description: "{description}"
{extra}

Return ONLY this JSON object (no extra text):
{{
  "category": "Gaming Laptops",
  "keywords": ["gaming laptop", "asus rog", "high performance", "rtx graphics", "gaming", "esports"],
  "confidence": 0.95
}}

Rules for category:
- Invent the most specific, descriptive category that fits this ad
- Be as granular as makes sense (e.g. "Running Shoes" not just "Footwear",
  "Noise-Cancelling Headphones" not just "Electronics")
- Use Title Case, 1-4 words, no punctuation
- Do NOT pick from any fixed list — create the best category for this ad

Rules for keywords:
- 8 to 15 lowercase keywords and short phrases
- Include: specific product type, brand (if given), model/variant, use-case,
  target audience, related accessories or complementary products
- Avoid generic filler like "best", "buy", "online", "cheap", "great"
- Mix broad terms (for reach) and specific terms (for precision)

JSON only:"""

    # ──────────────────────────────────────────────────────────────────────
    # Parsing
    # ──────────────────────────────────────────────────────────────────────

    def _parse(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            text = text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            m = re.search(r"\{[\s\S]*?\}", text)
            if m:
                text = m.group(0)
            data = json.loads(text)

            category = str(data.get("category", "")).strip()
            raw_kws = data.get("keywords", [])
            keywords: List[str] = [
                str(k).strip().lower() for k in raw_kws if str(k).strip()
            ][:20]
            confidence = float(data.get("confidence", 0.8))

            if not category:
                return None

            return {
                "category": category.title(),
                "keywords": list(dict.fromkeys(keywords)),  # dedup
                "confidence": round(confidence, 3),
            }
        except Exception as exc:
            logger.warning(f"JSON parse error in AdGeneratorService: {exc} — raw: {text[:200]}")
            return None

    # ──────────────────────────────────────────────────────────────────────
    # Heuristic fallback (no LLM)
    # ──────────────────────────────────────────────────────────────────────

    def _heuristic_fallback(
        self,
        title: str,
        description: str,
        brand: Optional[str],
    ) -> Dict[str, Any]:
        """
        Derive category and keywords directly from the ad text when LLM is unavailable.
        Category is built from the most meaningful nouns in the title rather than
        a fixed lookup table, so it stays specific to the actual ad content.
        """
        combined = f"{title} {description}".lower()

        # Use the first 2-3 meaningful words of the title as a specific category
        stopwords = {
            "the", "a", "an", "and", "or", "for", "in", "on", "at", "to", "of",
            "is", "are", "with", "by", "from", "your", "our", "we", "you", "it",
            "be", "as", "this", "that", "get", "now", "new", "best", "top",
            "buy", "free", "great", "good", "all", "more",
        }
        title_words = re.findall(r"[a-zA-Z][a-zA-Z0-9\-]{2,}", title)
        category_words = [w.title() for w in title_words if w.lower() not in stopwords][:3]
        category = " ".join(category_words) if category_words else "General"

        # Extract meaningful tokens from combined text as keywords
        words = re.findall(r"[a-z][a-z0-9\-]{2,}", combined)
        keywords = list(dict.fromkeys(w for w in words if w not in stopwords))[:15]

        if brand:
            brand_kw = brand.lower().strip()
            if brand_kw not in keywords:
                keywords.insert(0, brand_kw)

        return {
            "category": category,
            "keywords": keywords,
            "confidence": 0.4,
            "llm_used": False,
        }