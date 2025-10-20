"""OCR services for document text extraction"""

from .azure_service import AzureDocumentIntelligenceService, OCRResult, OCRPage, OCRLine, OCRWord
from .markdown_formatter import (
    OCRMarkdownFormatter,
    create_llm_grounding_prompt,
    format_for_dual_input
)

__all__ = [
    'AzureDocumentIntelligenceService',
    'OCRResult',
    'OCRPage',
    'OCRLine',
    'OCRWord',
    'OCRMarkdownFormatter',
    'create_llm_grounding_prompt',
    'format_for_dual_input'
]
