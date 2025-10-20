"""
Optimization Result Models

Represents the output of GEPA optimization including metrics,
optimized program, and performance data.
"""

from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class FieldMetrics(BaseModel):
    """Metrics for a single field"""
    field_name: str
    accuracy: float = Field(..., ge=0, le=1, description="Field accuracy (0-1)")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Average confidence")


class OptimizationMetrics(BaseModel):
    """Performance metrics from optimization"""
    baseline_accuracy: float = Field(..., ge=0, le=1, description="Accuracy before optimization")
    optimized_accuracy: float = Field(..., ge=0, le=1, description="Accuracy after optimization")
    improvement: float = Field(..., description="Accuracy improvement (percentage points)")

    # Per-field metrics
    field_metrics: List[FieldMetrics] = Field(
        default_factory=list,
        description="Accuracy breakdown by field"
    )

    # Training info
    training_examples_used: int = Field(..., description="Number of training examples")
    validation_examples_used: int = Field(..., description="Number of validation examples")

    # Optimization stats
    iterations_completed: Optional[int] = None
    optimization_time_seconds: Optional[float] = None


class OptimizationResult(BaseModel):
    """Complete result of GEPA optimization"""
    # Success status
    success: bool = Field(..., description="Whether optimization completed successfully")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    # Metrics
    metrics: Optional[OptimizationMetrics] = None

    # Optimized artifacts
    optimized_program_path: Optional[str] = Field(
        None,
        description="Path to saved DSPy program (.json file)"
    )
    optimized_prompts: Optional[Dict[str, str]] = Field(
        None,
        description="Optimized prompt for each field"
    )

    # Metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    config_used: Optional[Dict] = Field(
        None,
        description="Configuration used for optimization (for reproducibility)"
    )

    def duration_seconds(self) -> Optional[float]:
        """Calculate optimization duration in seconds"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


# Example usage:
if __name__ == "__main__":
    # Example: Successful optimization result
    result = OptimizationResult(
        success=True,
        metrics=OptimizationMetrics(
            baseline_accuracy=0.75,
            optimized_accuracy=0.92,
            improvement=17.0,
            field_metrics=[
                FieldMetrics(field_name="before_tax_total", accuracy=0.95),
                FieldMetrics(field_name="after_tax_total", accuracy=0.89)
            ],
            training_examples_used=9,
            validation_examples_used=3,
            iterations_completed=10,
            optimization_time_seconds=180.5
        ),
        optimized_program_path="pipelines/receipt_optimized_v1.json",
        optimized_prompts={
            "before_tax_total": "Extract the subtotal before tax. Look for 'Subtotal' label...",
            "after_tax_total": "Extract the final total including tax. Look for 'Total' at bottom..."
        }
    )

    print(result.model_dump_json(indent=2))
