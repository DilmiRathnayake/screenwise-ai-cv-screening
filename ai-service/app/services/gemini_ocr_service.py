"""Gemini-assisted text extraction for scanned or poor-quality CVs."""

from __future__ import annotations

import base64
from typing import Optional

from app.configs.settings import get_settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

EXTRACTION_PROMPT = (
    "Extract all readable text from this CV/resume document. "
    "Return plain text only, preserving section headings and line breaks. "
    "Do not summarize or omit content."
)


class GeminiOCRService:
    """Optional Gemini vision/text fallback when native OCR is insufficient."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None
        self._ready = False
        self._configure()

    @property
    def is_available(self) -> bool:
        return self._ready and bool(self.settings.gemini_api_key)

    def _configure(self) -> None:
        if not self.settings.gemini_api_key:
            logger.info("GEMINI_API_KEY not set — Gemini OCR fallback disabled")
            return
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.settings.gemini_api_key)
            self._client = genai.GenerativeModel(self.settings.gemini_model)
            self._ready = True
            logger.info("Gemini OCR fallback available (model=%s)", self.settings.gemini_model)
        except Exception as exc:
            self._ready = False
            logger.warning("Gemini OCR unavailable: %s", exc)

    def extract_from_image_bytes(self, content: bytes, mime_type: str = "image/png") -> Optional[str]:
        if not self.is_available or not self._client:
            return None
        try:
            import google.generativeai as genai

            part = {"mime_type": mime_type, "data": content}
            response = self._client.generate_content([EXTRACTION_PROMPT, part])
            text = (response.text or "").strip()
            return text if len(text) >= 50 else None
        except Exception as exc:
            logger.warning("Gemini image extraction failed: %s", exc)
            return None

    def extract_from_pdf_bytes(self, content: bytes) -> Optional[str]:
        if not self.is_available or not self._client:
            return None
        try:
            import google.generativeai as genai

            part = {"mime_type": "application/pdf", "data": content}
            response = self._client.generate_content([EXTRACTION_PROMPT, part])
            text = (response.text or "").strip()
            return text if len(text) >= 50 else None
        except Exception as exc:
            logger.warning("Gemini PDF extraction failed: %s", exc)
            return None

    def refine_text(self, partial_text: str) -> Optional[str]:
        """Improve noisy OCR output when enough context exists."""
        if not self.is_available or not self._client or len(partial_text) < 30:
            return None
        try:
            prompt = (
                "The following text was extracted from a CV/resume with OCR errors. "
                "Return corrected plain text only, preserving all factual content:\n\n"
                f"{partial_text[:12000]}"
            )
            response = self._client.generate_content(prompt)
            text = (response.text or "").strip()
            return text if len(text) > len(partial_text) * 0.8 else None
        except Exception as exc:
            logger.warning("Gemini text refinement failed: %s", exc)
            return None
