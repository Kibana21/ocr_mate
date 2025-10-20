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
]
