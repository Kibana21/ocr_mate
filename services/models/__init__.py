"""
Data Models for OCR Mate Services
"""

from .schema import (
    FieldType,
    FieldValidation,
    FieldDefinition,
    ExtractionSchema,
    GroundTruthExample
)
from .optimization_config import (
    LLMConfig,
    ImageProcessingConfig,
    GEPAConfig,
    OptimizationConfig
)
from .optimization_result import (
    FieldMetrics,
    OptimizationMetrics,
    OptimizationResult
)
from .annotation import (
    AnnotationSource,
    FieldAnnotation,
    DocumentAnnotation,
    OCRAssistedAnnotationService
)
from .verification import (
    VerificationStatus,
    FieldVerification,
    DocumentVerification,
    ConflictResolutionStrategy,
    DualExtractionVerifier
)

__all__ = [
    # Schema models
    'FieldType',
    'FieldValidation',
    'FieldDefinition',
    'ExtractionSchema',
    'GroundTruthExample',
    # Config models
    'LLMConfig',
    'ImageProcessingConfig',
    'GEPAConfig',
    'OptimizationConfig',
    # Result models
    'FieldMetrics',
    'OptimizationMetrics',
    'OptimizationResult',
    # Annotation models
    'AnnotationSource',
    'FieldAnnotation',
    'DocumentAnnotation',
    'OCRAssistedAnnotationService',
    # Verification models
    'VerificationStatus',
    'FieldVerification',
    'DocumentVerification',
    'ConflictResolutionStrategy',
    'DualExtractionVerifier',
]
