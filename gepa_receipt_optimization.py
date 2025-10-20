"""
GEPA Optimization for Receipt Totals Extraction
================================================

This script uses DSPy's GEPA optimizer to automatically improve receipt
extraction prompts based on ground truth examples.

Based on prompt_optimization.ipynb structure:
- Cells 0-8: Setup, data models, metric
- Cells 9-20: Pixeltable tracking (optional)
- Cells 42-68: DSPy GEPA optimization

Usage:
    python gepa_receipt_optimization.py

Requirements:
    pip install dspy-ai litellm pillow pixeltable pydantic

Environment:
    export GROQ_API_KEY="your-groq-key"
    export OPENAI_API_KEY="your-openai-key"
"""

import os
import io
import base64
from typing import Optional, Dict
from PIL import Image

import dspy
import pixeltable as pxt
from pixeltable import func
from pydantic import BaseModel, field_validator
import litellm


# ============================================================================
# PART 1: Data Model (from cells 6-7 of prompt_optimization.ipynb)
# ============================================================================

class ReceiptTotals(BaseModel):
    """
    Pydantic model for receipt totals extraction.
    Same as in prompt_optimization.ipynb cell 6.
    """
    before_tax_total: Optional[float] = None
    after_tax_total: Optional[float] = None

    @field_validator('before_tax_total', 'after_tax_total', mode='before')
    @classmethod
    def extract_from_xml(cls, v):
        """Extract value from XML tags if present."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            import re
            # Remove XML tags if present
            v = re.sub(r'<[^>]+>', '', v)
            # Remove currency symbols and commas
            v = re.sub(r'[$,]', '', v.strip())
            try:
                return float(v)
            except ValueError:
                return None
        return None


# ============================================================================
# PART 2: Metric Functions (from cells 7-8)
# ============================================================================

def metric(ground_truth: ReceiptTotals, pred: ReceiptTotals) -> float:
    """
    Simple binary metric from cell 7 of prompt_optimization.ipynb.
    Returns 1.0 if both totals match exactly, 0.0 otherwise.
    """
    is_btax_same = ground_truth.before_tax_total == pred.before_tax_total
    is_atax_same = ground_truth.after_tax_total == pred.after_tax_total
    return float(is_btax_same and is_atax_same)


def metric_with_feedback(gold, pred, trace, pred_name, pred_trace):
    """
    GEPA-compatible metric with 5 parameters and textual feedback.

    This is the enhanced version for GEPA optimization.

    Args:
        gold: Ground truth dspy.Example with receipt_totals
        pred: Prediction with receipt_totals
        trace: Legacy parameter (may be None)
        pred_name: Name of predictor
        pred_trace: Detailed trace with reasoning

    Returns:
        dspy.Prediction(score=float, feedback=str)
    """
    # Extract ReceiptTotals from gold and pred
    gold_totals = gold.receipt_totals if hasattr(gold, 'receipt_totals') else gold
    pred_totals = pred.receipt_totals if hasattr(pred, 'receipt_totals') else pred

    # Check both fields
    is_btax_same = gold_totals.before_tax_total == pred_totals.before_tax_total
    is_atax_same = gold_totals.after_tax_total == pred_totals.after_tax_total

    # Calculate score
    score = float(is_btax_same and is_atax_same)

    # Generate feedback
    feedback_parts = []

    if not is_btax_same:
        feedback_parts.append(
            f"Before-tax total incorrect. "
            f"Expected: ${gold_totals.before_tax_total:.2f}, "
            f"Got: ${pred_totals.before_tax_total if pred_totals.before_tax_total else 'None'}. "
            f"Look for 'Subtotal' label, usually appears before tax line."
        )

    if not is_atax_same:
        feedback_parts.append(
            f"After-tax total incorrect. "
            f"Expected: ${gold_totals.after_tax_total:.2f}, "
            f"Got: ${pred_totals.after_tax_total if pred_totals.after_tax_total else 'None'}. "
            f"Look for 'Total', 'Amount', or 'Balance' label at the bottom."
        )

    if score == 1.0:
        feedback = "Both totals extracted correctly!"
    else:
        feedback = " ".join(feedback_parts)
        feedback += " Tax is typically 8-10% of subtotal."

    return dspy.Prediction(score=score, feedback=feedback)


# ============================================================================
# PART 3: Helper Function for Baseline Extraction (Pixeltable UDF)
# ============================================================================

def extract_totals_baseline(img: Image.Image) -> Dict[str, float]:
    """
    Baseline extraction for Pixeltable tracking.
    Uses simple default prompt before GEPA optimization.

    Args:
        img: PIL Image of receipt

    Returns:
        Dict with 'before_tax_total' and 'after_tax_total'
    """
    # Simple baseline prompt
    prompt = (
        "Extract the after-tax total and the before-tax total from the receipt.\n"
        "Return the values inside these XML tags:\n"
        "<before_tax_total>VALUE</before_tax_total>\n"
        "<after_tax_total>VALUE</after_tax_total>"
    )

    # Convert image to base64
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=95)
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Prepare messages
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        ]
    }]

    # Call LLM
    response = litellm.completion(
        model="groq/llama-4-scout-17b-16e-instruct",
        messages=messages,
        temperature=0
    )

    response_text = response.choices[0]["message"]["content"]

    # Parse response
    try:
        receipt_totals = ReceiptTotals(
            before_tax_total=response_text,
            after_tax_total=response_text
        )
        return receipt_totals.model_dump()
    except:
        return {'before_tax_total': None, 'after_tax_total': None}


# ============================================================================
# PART 4: Pixeltable Setup (from cells 9-20)
# ============================================================================

def setup_pixeltable():
    """
    Set up Pixeltable for tracking optimization results.
    Based on cells 9-20 from prompt_optimization.ipynb.
    """
    # Drop existing table (from cell 9)
    pxt.drop_dir('receipt_gepa', force=True)
    pxt.create_dir('receipt_gepa')

    # Create table (from cell 9)
    t = pxt.create_table('receipt_gepa.receipts', {
        'receipt_path': pxt.String,
        'receipt_image': pxt.Image
    })

    return t


def add_baseline_extraction(table):
    """
    Add baseline extraction column to table.
    Based on cells 10-13 from prompt_optimization.ipynb.
    """
    # Create UDF for extraction (from cell 12)
    @pxt.udf
    def extract_totals_udf(img: Image.Image) -> Dict[str, float]:
        return extract_totals_baseline(img)

    # Add computed column (from cell 12)
    table.add_computed_column(extraction=extract_totals_udf(table.receipt_image))

    return table


def add_ground_truth_and_metric(table, ground_truth_data):
    """
    Add ground truth and metric columns.
    Based on cells 14-17 from prompt_optimization.ipynb.
    """
    # Add ground truth column (from cell 14)
    table.add_column(ground_truth=pxt.Json)

    # Update with ground truth data (from cell 14)
    for item in ground_truth_data:
        table.update(
            {'receipt_path': item['receipt_path']},
            {'ground_truth': item['ground_truth']}
        )

    # Create metric UDF (from cell 15)
    @pxt.udf
    def metric_udf(gt: dict, pred: dict) -> float:
        return metric(ReceiptTotals(**gt), ReceiptTotals(**pred))

    # Add metric column (from cell 16)
    table.add_computed_column(is_same=metric_udf(table.ground_truth, table.extraction))

    return table


# ============================================================================
# PART 5: DSPy with GEPA (cells 42-68 adapted)
# ============================================================================

class ReceiptExtraction(dspy.Signature):
    """
    DSPy signature for receipt totals extraction.
    Similar to cell 43 from prompt_optimization.ipynb.
    """
    receipt_image: dspy.Image = dspy.InputField(
        desc="Receipt image to extract totals from"
    )
    receipt_totals: ReceiptTotals = dspy.OutputField(
        desc="Before-tax and after-tax totals"
    )


def create_training_data():
    """
    Create DSPy training dataset.
    Based on cell 54 from prompt_optimization.ipynb.
    """
    # Ground truth data (from cell 54)
    goldset = [
        {'receipt_path': 'images/receipts/IMG_2171.jpg', 'ground_truth': {'before_tax_total': 25.0, 'after_tax_total': 25.30}},
        {'receipt_path': 'images/receipts/IMG_2170.jpg', 'ground_truth': {'before_tax_total': 246.62, 'after_tax_total': 258.96}},
        {'receipt_path': 'images/receipts/IMG_2172.jpg', 'ground_truth': {'before_tax_total': 80.0, 'after_tax_total': 88.8}},
        {'receipt_path': 'images/receipts/IMG_2166.jpg', 'ground_truth': {'before_tax_total': 559.93, 'after_tax_total': 561.64}},
        {'receipt_path': 'images/receipts/IMG_2167.jpg', 'ground_truth': {'before_tax_total': 195.0, 'after_tax_total': 232.92}},
        {'receipt_path': 'images/receipts/IMG_2173.jpg', 'ground_truth': {'before_tax_total': 2805, 'after_tax_total': 3394.06}},
        {'receipt_path': 'images/receipts/IMG_2163.jpg', 'ground_truth': {'before_tax_total': 1660.0, 'after_tax_total': 2134.0}},
        {'receipt_path': 'images/receipts/IMG_2160.jpg', 'ground_truth': {'before_tax_total': 2011.0, 'after_tax_total': 2521.61}},
        {'receipt_path': 'images/receipts/IMG_2174.jpg', 'ground_truth': {'before_tax_total': 9520.00, 'after_tax_total': 10576.00}},
        {'receipt_path': 'images/receipts/IMG_2175.jpg', 'ground_truth': {'before_tax_total': 1315.00, 'after_tax_total': 1381.00}},
        {'receipt_path': 'images/receipts/IMG_2169.jpg', 'ground_truth': {'before_tax_total': 1265.00, 'after_tax_total': 1530.65}},
        {'receipt_path': 'images/receipts/IMG_2168.jpg', 'ground_truth': {'before_tax_total': 2011.00, 'after_tax_total': 2522.00}},
    ]

    # Convert to DSPy Examples (from cell 54)
    evalset = []
    for item in goldset:
        try:
            img = dspy.Image.from_file(item["receipt_path"])
        except:
            print(f"Warning: Could not load {item['receipt_path']}, skipping...")
            continue

        example = dspy.Example(
            receipt_image=img,
            receipt_totals=ReceiptTotals(
                before_tax_total=item["ground_truth"]["before_tax_total"],
                after_tax_total=item["ground_truth"]["after_tax_total"]
            )
        ).with_inputs("receipt_image")

        evalset.append(example)

    return evalset, goldset


def run_gepa_optimization():
    """
    Run GEPA optimization on receipt extraction.

    This function:
    1. Sets up student (Llama) and reflection (GPT-4o) LLMs
    2. Loads training data from receipt images
    3. Creates baseline DSPy program
    4. Runs GEPA optimization to improve prompts
    5. Evaluates and saves optimized program
    6. Tracks results in Pixeltable (optional)

    Based on cells 42-68 from prompt_optimization.ipynb.
    """
    print("=" * 80)
    print("GEPA OPTIMIZATION FOR RECEIPT TOTALS EXTRACTION")
    print("=" * 80)
    print()

    # Step 1: Set up LLMs (from cell 42)
    print("[1/7] Setting up language models...")
    student_lm = dspy.LM(
        model="groq/llama-4-scout-17b-16e-instruct",
        api_key=os.environ.get("GROQ_API_KEY")
    )

    # For GEPA optimization
    reflection_lm = dspy.LM(
        model="openai/gpt-4o",
        api_key=os.environ.get("OPENAI_API_KEY")
    )
    print("  ✓ Student model: Llama 4 Scout (fast, cheap)")
    print("  ✓ Reflection model: GPT-4o (smart, for optimization)")

    # Step 2: Create training data (from cell 54)
    print("\n[2/7] Loading training data...")
    evalset, goldset = create_training_data()
    print(f"  ✓ Loaded {len(evalset)} receipt examples")

    # Split into train and validation
    split_idx = int(len(evalset) * 0.8)
    trainset = evalset[:split_idx]
    valset = evalset[split_idx:]
    print(f"  ✓ Training set: {len(trainset)} examples")
    print(f"  ✓ Validation set: {len(valset)} examples")

    # Step 3: Create baseline program (from cells 43-45)
    print("\n[3/7] Creating baseline DSPy program...")
    dprogram = dspy.Predict(ReceiptExtraction)
    dprogram.set_lm(student_lm)
    print("  ✓ Created dspy.Predict(ReceiptExtraction)")

    # Step 4: Test baseline (from cells 48-53)
    print("\n[4/7] Testing baseline program...")
    if trainset:
        test_pred = dprogram(receipt_image=trainset[0].receipt_image)
        print("  Sample prediction:")
        print(f"    Before-tax: ${test_pred.receipt_totals.before_tax_total}")
        print(f"    After-tax: ${test_pred.receipt_totals.after_tax_total}")

    # Calculate baseline accuracy
    baseline_scores = []
    for example in trainset:
        pred = dprogram(receipt_image=example.receipt_image)
        result = metric_with_feedback(
            gold=example,
            pred=pred,
            trace=None,
            pred_name="baseline",
            pred_trace=None
        )
        baseline_scores.append(result.score)

    baseline_accuracy = sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0
    baseline_correct = sum(baseline_scores)
    print(f"  Baseline: {baseline_correct}/{len(trainset)} correct ({baseline_accuracy*100:.1f}%)")

    # Step 5: Set up Pixeltable tracking (optional, from cells 9-20)
    print("\n[5/7] Setting up Pixeltable tracking...")
    try:
        t = setup_pixeltable()

        # Insert data
        for item in goldset[:len(trainset)]:
            t.insert(
                receipt_path=item['receipt_path'],
                receipt_image=item['receipt_path']
            )

        t = add_baseline_extraction(t)
        t = add_ground_truth_and_metric(t, goldset[:len(trainset)])

        print("  ✓ Pixeltable tracking enabled")
        print(f"  ✓ Baseline tracked in table: receipt_gepa.receipts")
    except Exception as e:
        print(f"  ⚠ Pixeltable setup failed: {e}")
        print("  Continuing without Pixeltable tracking...")
        t = None

    # Step 6: Create GEPA optimizer (adapted from cell 58)
    print("\n[6/7] Setting up GEPA optimizer...")

    # Optional: Create teacher program for better optimization
    teacherp = dprogram.deepcopy()
    teacherp.set_lm(dspy.LM("openai/gpt-4o"))

    optimizer = dspy.GEPA(
        metric=metric_with_feedback,      # Our 5-parameter metric
        auto="light",                     # light/medium/heavy
        num_threads=4,                    # Parallel evaluation
        reflection_minibatch_size=3,      # Examples per reflection
        reflection_lm=reflection_lm,      # GPT-4o for optimization
        track_stats=True,                 # Log progress
        max_bootstrapped_demos=0,         # No synthetic examples
        max_labeled_demos=0               # No few-shot examples
    )
    print("  ✓ GEPA optimizer configured")
    print("    - Auto level: light (5-10 min)")
    print("    - Minibatch size: 3")
    print("    - Using teacher model (GPT-4o)")

    # Step 7: Run optimization (from cell 58)
    print("\n[7/7] Running GEPA optimization...")
    print("  This will take 5-15 minutes...")
    print("  GEPA process:")
    print("    1. Run baseline on training examples")
    print("    2. Identify failures and collect feedback")
    print("    3. GPT-4o analyzes failures in natural language")
    print("    4. Propose improved prompts")
    print("    5. Test candidates and maintain Pareto frontier")
    print("    6. Combine complementary lessons")
    print()

    try:
        dprogram_optimized = optimizer.compile(
            student=dprogram,
            trainset=trainset,
            valset=valset if valset else None,
            requires_permission_to_run=False,
            teacher=teacherp
        )

        print("\n✓ GEPA optimization complete!")

        # Step 8: Test optimized program (from cells 63-66)
        print("\n[8/7] Testing optimized program...")
        optimized_scores = []
        for example in trainset:
            pred = dprogram_optimized(receipt_image=example.receipt_image)
            result = metric_with_feedback(
                gold=example,
                pred=pred,
                trace=None,
                pred_name="optimized",
                pred_trace=None
            )
            optimized_scores.append(result.score)

        optimized_accuracy = sum(optimized_scores) / len(optimized_scores) if optimized_scores else 0
        optimized_correct = sum(optimized_scores)

        print(f"  Baseline:  {baseline_correct}/{len(trainset)} correct ({baseline_accuracy*100:.1f}%)")
        print(f"  Optimized: {optimized_correct}/{len(trainset)} correct ({optimized_accuracy*100:.1f}%)")
        print(f"  Improvement: +{(optimized_accuracy - baseline_accuracy)*100:.1f}%")

        # Inspect optimized prompt (from cell 62)
        print("\n" + "=" * 80)
        print("OPTIMIZED PROMPT")
        print("=" * 80)
        for name, predictor in dprogram_optimized.named_predictors():
            print(f"\nPredictor: {name}")
            print(f"\nInstructions:")
            print(predictor.signature.instructions)
            if hasattr(predictor, 'demos') and predictor.demos:
                print(f"\nDemonstrations: {len(predictor.demos)}")
        print("=" * 80)

        # Add optimized extraction to Pixeltable (like cells 30, 36, 40)
        if t is not None:
            try:
                @pxt.udf
                def extract_totals_optimized_udf(img: Image.Image) -> Dict[str, float]:
                    result = dprogram_optimized(receipt_image=dspy.Image.from_PIL(img))
                    return result.receipt_totals.model_dump()

                t.add_computed_column(extraction_gepa=extract_totals_optimized_udf(t.receipt_image))
                t.add_computed_column(is_same_gepa=metric_udf(t.ground_truth, t.extraction_gepa))

                print("\n✓ Added GEPA results to Pixeltable")
                print("  Compare versions: t.select(t.is_same, t.is_same_gepa).show()")
            except Exception as e:
                print(f"\n⚠ Could not add to Pixeltable: {e}")

        # Save optimized program (from cell 67)
        output_path = "receipt_pipeline_gepa_optimized.json"
        dprogram_optimized.save(output_path)
        print(f"\n✓ Optimized program saved to: {output_path}")

        return dprogram_optimized, t

    except Exception as e:
        print(f"\n✗ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        raise


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n🎯 Receipt Totals Extraction with GEPA Optimizer")
    print("Automated prompt optimization using DSPy GEPA\n")

    # Check API keys
    if "GROQ_API_KEY" not in os.environ:
        print("⚠ Warning: GROQ_API_KEY not set")
        print("  Set with: export GROQ_API_KEY='your-key'")

    if "OPENAI_API_KEY" not in os.environ:
        print("⚠ Warning: OPENAI_API_KEY not set (required for GEPA)")
        print("  Set with: export OPENAI_API_KEY='your-key'")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            exit(1)

    try:
        dprogram_optimized, table = run_gepa_optimization()

        print("\n" + "=" * 80)
        print("✓ SUCCESS!")
        print("=" * 80)
        print("\nYour receipt extraction pipeline has been optimized using GEPA.")
        print("\nUsage:")
        print("  import dspy")
        print("  from PIL import Image")
        print()
        print("  # Load optimized program")
        print("  program = dspy.load('receipt_pipeline_gepa_optimized.json')")
        print("  program.set_lm(dspy.LM('groq/llama-4-scout-17b-16e-instruct'))")
        print()
        print("  # Extract from new receipt")
        print("  img = dspy.Image.from_file('new_receipt.jpg')")
        print("  result = program(receipt_image=img)")
        print("  print(f'Before tax: ${result.receipt_totals.before_tax_total}')")
        print("  print(f'After tax: ${result.receipt_totals.after_tax_total}')")

        if table is not None:
            print("\nPixeltable comparison:")
            print("  import pixeltable as pxt")
            print("  t = pxt.get_table('receipt_gepa.receipts')")
            print("  t.select(t.receipt_path, t.is_same, t.is_same_gepa).show()")

    except KeyboardInterrupt:
        print("\n\n⚠ Optimization interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
