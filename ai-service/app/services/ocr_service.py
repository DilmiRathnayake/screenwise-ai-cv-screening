"""OCR and document text extraction router."""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Optional, Tuple

import fitz  # PyMuPDF
from docx import Document
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from app.configs.settings import get_settings
from app.services.gemini_ocr_service import GeminiOCRService
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
MIN_RELIABLE_TEXT_LEN = 200


class OCRService:
    """Route documents to PyMuPDF, python-docx, Tesseract, or Gemini fallback."""

    def __init__(self, gemini: Optional[GeminiOCRService] = None) -> None:
        self.settings = get_settings()
        self._tesseract_ready = False
        self.gemini = gemini or GeminiOCRService()
        self._configure_tesseract()

    def _configure_tesseract(self) -> None:
        try:
            import pytesseract

            if self.settings.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.settings.tesseract_cmd
            pytesseract.get_tesseract_version()
            self._tesseract_ready = True
            logger.info("Tesseract OCR available")
        except Exception as exc:  # pragma: no cover
            self._tesseract_ready = False
            logger.warning("Tesseract not available — image OCR disabled: %s", exc)

    def extract_text(self, filename: str, content: bytes) -> Tuple[str, str]:
        """
        Extract text from file bytes.

        Returns:
            (text, method) where method is one of:
            pymupdf, python-docx, tesseract, hybrid, gemini
        """
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{ext}'. Accepted: {sorted(SUPPORTED_EXTENSIONS)}"
            )

        if ext == ".pdf":
            text, method = self._extract_pdf(content)
        elif ext == ".docx":
            text, method = self._extract_docx(content), "python-docx"
        else:
            text, method = self._extract_image(content), "tesseract"

        if not self._is_reliable_text(text):
            improved = self._try_gemini_fallback(content, ext, text)
            if improved:
                return improved
        return text, method

    def _is_reliable_text(self, text: str) -> bool:
        stripped = (text or "").strip()
        if len(stripped) < MIN_RELIABLE_TEXT_LEN:
            return False
        alpha = sum(1 for c in stripped if c.isalpha())
        if alpha / max(len(stripped), 1) < 0.35:
            return False
        words = re.findall(r"[A-Za-z]{2,}", stripped)
        return len(words) >= 30

    def _try_gemini_fallback(
        self, content: bytes, ext: str, partial: str
    ) -> Optional[Tuple[str, str]]:
        if not self.gemini.is_available:
            return None
        try:
            if ext == ".pdf":
                text = self.gemini.extract_from_pdf_bytes(content)
                if text:
                    return text, "gemini"
            elif ext in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
                mime = "image/png" if ext == ".png" else "image/jpeg"
                text = self.gemini.extract_from_image_bytes(content, mime_type=mime)
                if text:
                    return text, "gemini"
            elif partial:
                refined = self.gemini.refine_text(partial)
                if refined:
                    return refined, "gemini"
        except Exception as exc:
            logger.warning("Gemini fallback failed: %s", exc)
        return None

    def _extract_pdf(self, content: bytes) -> Tuple[str, str]:
        doc = fitz.open(stream=content, filetype="pdf")
        texts: list[str] = []
        image_pages = 0
        try:
            for page in doc:
                page_text = page.get_text("text") or ""
                if page_text.strip():
                    texts.append(page_text)
                else:
                    image_pages += 1
                    if self._tesseract_ready:
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        img_bytes = pix.tobytes("png")
                        ocr_text = self._ocr_image_bytes(img_bytes)
                        if ocr_text.strip():
                            texts.append(ocr_text)
        finally:
            doc.close()

        combined = "\n".join(texts).strip()
        if image_pages and any(t for t in texts):
            method = "hybrid"
        elif image_pages and not combined:
            method = "tesseract"
        else:
            method = "pymupdf"
        return combined, method

    def _extract_docx(self, content: bytes) -> str:
        document = Document(io.BytesIO(content))
        parts: list[str] = []
        for para in document.paragraphs:
            if para.text and para.text.strip():
                parts.append(para.text.strip())
        for table in document.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text and c.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return "\n".join(parts)

    def _extract_image(self, content: bytes) -> str:
        if not self._tesseract_ready:
            if self.gemini.is_available:
                text = self.gemini.extract_from_image_bytes(content)
                if text:
                    return text
            raise RuntimeError(
                "Tesseract OCR is not installed or not configured. "
                "Install Tesseract and set TESSERACT_CMD if needed."
            )
        return self._ocr_image_bytes(content)

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Improve OCR quality: grayscale, contrast, sharpen, light denoise."""
        img = image.convert("L")
        img = ImageOps.autocontrast(img)
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = img.filter(ImageFilter.MedianFilter(size=3))
        img = ImageEnhance.Sharpness(img).enhance(1.2)
        w, h = img.size
        if max(w, h) < 1200:
            scale = 1200 / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        return img

    def _ocr_image_bytes(self, content: bytes) -> str:
        import pytesseract

        with Image.open(io.BytesIO(content)) as image:
            processed = self.preprocess_image(image)
            text = pytesseract.image_to_string(
                processed, lang=self.settings.ocr_language
            )
        return text or ""
