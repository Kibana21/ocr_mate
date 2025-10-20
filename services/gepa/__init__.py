"""
GEPA Optimization Services

Reusable GEPA optimization components for any document type.
"""

from .optimizer import GEPAOptimizer
from .schema_adapter import SchemaAdapter
from .metric_factory import create_metric_function
from .training_data import TrainingDataConverter
from .image_processor import (
    resize_image_for_llm,
    load_and_resize_image,
    pil_to_dspy_image
)

__all__ = [
    'GEPAOptimizer',
    'SchemaAdapter',
    'create_metric_function',
    'TrainingDataConverter',
    'resize_image_for_llm',
    'load_and_resize_image',
    'pil_to_dspy_image',
]
