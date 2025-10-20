"""OCR services for document text extraction"""

from .azure_service import AzureDocumentIntelligenceService, OCRResult, OCRPage, OCRLine, OCRWord

__all__ = [
    'AzureDocumentIntelligenceService',
    'OCRResult',
    'OCRPage',
    'OCRLine',
    'OCRWord'
]
