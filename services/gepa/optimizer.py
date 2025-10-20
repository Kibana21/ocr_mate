"""
GEPA Optimizer - Main orchestrator for GEPA optimization

This is the main entry point for running GEPA optimization on any document type.
Extracted and generalized from gepa_receipt_optimization.py
"""

import os
import dspy
import litellm
import time
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from services.models.schema import ExtractionSchema, GroundTruthExample
from services.models.optimization_config import OptimizationConfig
from services.models.optimization_result import (
    OptimizationResult,
    OptimizationMetrics,
    FieldMetrics
)
from services.gepa.schema_adapter import SchemaAdapter
from services.gepa.metric_factory import create_metric_function
from services.gepa.training_data import TrainingDataConverter


class GEPAOptimizer:
    """
    GEPA Optimizer for document extraction pipelines.

    Usage:
        optimizer = GEPAOptimizer(schema, config)
        result = optimizer.optimize(ground_truth_examples)
    """

    def __init__(
        self,
        schema: ExtractionSchema,
        config: OptimizationConfig,
        output_dir: str = "optimized_pipelines"
    ):
        """
        Initialize GEPA optimizer.

        Args:
            schema: ExtractionSchema defining fields to extract
            config: OptimizationConfig with LLM and GEPA settings
            output_dir: Directory to save optimized pipelines
        """
        self.schema = schema
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Will be created during optimization
        self.schema_adapter: Optional[SchemaAdapter] = None
        self.metric_function = None
        self.training_converter: Optional[TrainingDataConverter] = None

    def _setup_rate_limiting(self):
        """Configure rate limiting to avoid API errors"""
        original_completion = litellm.completion

        def rate_limited_completion(*args, **kwargs):
            time.sleep(self.config.delay_seconds)
            return original_completion(*args, **kwargs)

        litellm.completion = rate_limited_completion

    def _setup_llms(self) -> tuple[dspy.LM, dspy.LM]:
        """
        Setup student and reflection LLMs.

        Returns:
            Tuple of (student_lm, reflection_lm)
        """
        # Student LLM
        student_lm = dspy.LM(
            model=f"{self.config.student_llm.provider}/{self.config.student_llm.model_name}",
            api_key=self.config.student_llm.api_key,
            temperature=self.config.student_llm.temperature
        )

        # Reflection LLM
        reflection_lm = dspy.LM(
            model=f"{self.config.reflection_llm.provider}/{self.config.reflection_llm.model_name}",
            api_key=self.config.reflection_llm.api_key,
            temperature=self.config.reflection_llm.temperature
        )

        return student_lm, reflection_lm

    def _prepare_training_data(
        self,
        ground_truth_examples: List[GroundTruthExample]
    ) -> tuple[List[dspy.Example], List[dspy.Example]]:
        """
        Convert ground truth to DSPy format and split train/val.

        Args:
            ground_truth_examples: List of GroundTruthExample objects

        Returns:
            Tuple of (train_examples, val_examples)
        """
        # Convert to DSPy format
        dspy_examples = self.training_converter.convert(
            ground_truth_examples,
            test_mode=self.config.test_mode
        )

        # Split train/val
        train_examples, val_examples = self.training_converter.split_train_val(
            dspy_examples,
            train_fraction=self.config.train_val_split
        )

        return train_examples, val_examples

    def _test_program(
        self,
        program: dspy.Module,
        examples: List[dspy.Example]
    ) -> tuple[float, List[float]]:
        """
        Test a program on examples and calculate accuracy.

        Args:
            program: DSPy program to test
            examples: List of examples to test on

        Returns:
            Tuple of (accuracy, list of scores)
        """
        scores = []

        for example in examples:
            try:
                # Run prediction
                pred = program(document_image=example.document_image)

                # Calculate score
                score = self.metric_function(example, pred)
                scores.append(score)
            except Exception as e:
                print(f"⚠ Prediction failed: {e}")
                scores.append(0.0)

        accuracy = sum(scores) / len(scores) if scores else 0.0
        return accuracy, scores

    def optimize(
        self,
        ground_truth_examples: List[GroundTruthExample]
    ) -> OptimizationResult:
        """
        Run GEPA optimization.

        Args:
            ground_truth_examples: List of labeled examples

        Returns:
            OptimizationResult with metrics and optimized program
        """
        start_time = datetime.utcnow()

        try:
            print("=" * 80)
            print("GEPA OPTIMIZATION")
            print("=" * 80)
            print()

            # Configure rate limiting
            self._setup_rate_limiting()

            # Step 1: Setup LLMs
            print("[1/7] Setting up language models...")
            if self.config.test_mode:
                print(f"  ⚠ TEST MODE: Using only 4 examples")
            print(f"  Rate limiting: {self.config.delay_seconds}s delay between calls")

            student_lm, reflection_lm = self._setup_llms()
            print(f"  ✓ Student: {self.config.student_llm.provider}/{self.config.student_llm.model_name}")
            print(f"  ✓ Reflection: {self.config.reflection_llm.provider}/{self.config.reflection_llm.model_name}")

            # Step 2: Create DSPy components from schema
            print("\n[2/7] Creating DSPy signature from schema...")
            self.schema_adapter = SchemaAdapter(self.schema)
            extraction_model = self.schema_adapter.get_extraction_model()
            dspy_signature = self.schema_adapter.get_dspy_signature()
            print(f"  ✓ Created signature with {len(self.schema.fields)} fields")

            # Step 3: Create metric function
            print("\n[3/7] Creating metric function with feedback...")
            self.metric_function = create_metric_function(self.schema)
            print(f"  ✓ Metric created for {len(self.schema.fields)} fields")

            # Step 4: Prepare training data
            print("\n[4/7] Loading and preparing training data...")
            self.training_converter = TrainingDataConverter(
                self.schema,
                extraction_model,
                max_width=self.config.image_processing.max_width,
                max_height=self.config.image_processing.max_height,
                jpeg_quality=self.config.image_processing.jpeg_quality
            )

            train_examples, val_examples = self._prepare_training_data(ground_truth_examples)

            # Step 5: Create baseline program
            print("\n[5/7] Creating baseline DSPy program...")
            dprogram = dspy.Predict(dspy_signature)
            dprogram.set_lm(student_lm)
            print(f"  ✓ Baseline program created")

            # Test baseline
            print("\n[6/7] Testing baseline program...")
            baseline_accuracy, baseline_scores = self._test_program(dprogram, train_examples)
            baseline_correct = sum(baseline_scores)
            print(f"  Baseline: {baseline_correct}/{len(train_examples)} correct ({baseline_accuracy*100:.1f}%)")

            # Step 6: Setup GEPA optimizer
            print("\n[7/7] Running GEPA optimization...")
            optimizer = dspy.GEPA(
                metric=self.metric_function,
                auto=self.config.gepa.auto,
                num_threads=self.config.gepa.num_threads,
                reflection_minibatch_size=self.config.gepa.reflection_minibatch_size,
                reflection_lm=reflection_lm,
                track_stats=self.config.gepa.track_stats
            )
            print(f"  ✓ GEPA configured")
            print(f"    - Auto level: {self.config.gepa.auto}")
            print(f"    - Threads: {self.config.gepa.num_threads} (sequential)")
            print(f"    - Minibatch size: {self.config.gepa.reflection_minibatch_size}")

            # Run optimization
            print("\n  Starting optimization...")
            print("  This may take 15-30 minutes (rate limited)...")
            print()

            dprogram_optimized = optimizer.compile(
                student=dprogram,
                trainset=train_examples,
                valset=val_examples if val_examples else None
            )

            print("\n✓ GEPA optimization complete!")

            # Test optimized program
            print("\n[8/8] Testing optimized program...")
            optimized_accuracy, optimized_scores = self._test_program(dprogram_optimized, train_examples)
            optimized_correct = sum(optimized_scores)

            print(f"  Baseline:  {baseline_correct}/{len(train_examples)} correct ({baseline_accuracy*100:.1f}%)")
            print(f"  Optimized: {optimized_correct}/{len(train_examples)} correct ({optimized_accuracy*100:.1f}%)")
            improvement = (optimized_accuracy - baseline_accuracy) * 100
            print(f"  Improvement: {improvement:+.1f}%")

            # Save optimized program
            output_filename = f"pipeline_optimized_{int(time.time())}.json"
            output_path = self.output_dir / output_filename
            dprogram_optimized.save(str(output_path))
            print(f"\n✓ Optimized program saved to: {output_path}")

            # Create result
            end_time = datetime.utcnow()
            result = OptimizationResult(
                success=True,
                metrics=OptimizationMetrics(
                    baseline_accuracy=baseline_accuracy,
                    optimized_accuracy=optimized_accuracy,
                    improvement=improvement,
                    training_examples_used=len(train_examples),
                    validation_examples_used=len(val_examples),
                    optimization_time_seconds=(end_time - start_time).total_seconds()
                ),
                optimized_program_path=str(output_path),
                started_at=start_time,
                completed_at=end_time,
                config_used=self.config.model_dump()
            )

            return result

        except Exception as e:
            print(f"\n✗ Optimization failed: {e}")
            import traceback
            traceback.print_exc()

            # Return failure result
            return OptimizationResult(
                success=False,
                error_message=str(e),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )


# Example usage
if __name__ == "__main__":
    from services.models.schema import ExtractionSchema, FieldDefinition, FieldType, GroundTruthExample
    from services.models.optimization_config import OptimizationConfig, LLMConfig

    print("GEPA Optimizer Module")
    print("=" * 80)
    print("\nThis module provides reusable GEPA optimization for any document type.")
    print("\nExample usage:")
    print("""
    # 1. Define schema
    schema = ExtractionSchema(fields=[...])

    # 2. Configure optimization
    config = OptimizationConfig(
        student_llm=LLMConfig(provider="gemini", ...),
        reflection_llm=LLMConfig(provider="gemini", ...),
        test_mode=True
    )

    # 3. Run optimization
    optimizer = GEPAOptimizer(schema, config)
    result = optimizer.optimize(ground_truth_examples)

    # 4. Use optimized pipeline
    print(f"Accuracy improved from {result.metrics.baseline_accuracy} to {result.metrics.optimized_accuracy}")
    """)
