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
    pip install dspy-ai litellm pillow pixeltable pydantic python-dotenv

Environment:
    export GEMINI_API_KEY="your-gemini-key"
"""

import os
import io
import base64
from typing import Optional, Dict
from PIL import Image
from dotenv import load_dotenv

import dspy
import pixeltable as pxt
from pixeltable import func
from pydantic import BaseModel, field_validator
import litellm

# Load environment variables from .env file
load_dotenv()


# ============================================================================
# PART 1: Data Model (from cells 6-7 of prompt_optimization.ipynb)
# ============================================================================

class ReceiptTotals(BaseModel):
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


def metric_with_feedback(gold, pred, trace=None, pred_name=None, pred_trace=None):
    """
    GEPA-compatible metric with 5 parameters and textual feedback.

    This is the enhanced version for GEPA optimization.

    Args:
        gold: Ground truth dspy.Example with receipt_totals
        pred: Prediction with receipt_totals
        trace: Legacy parameter (may be None)
        pred_name: Name of predictor (optional) - when provided, returns feedback for that predictor
        pred_trace: Detailed trace with reasoning (optional)

    Returns:
        - If pred_name is None: returns float score
        - If pred_name is specified: returns dspy.Prediction(score=float, feedback=str)
    """
    # Extract ReceiptTotals from gold and pred
    gold_totals = gold.receipt_totals if hasattr(gold, 'receipt_totals') else gold
    pred_totals = pred.receipt_totals if hasattr(pred, 'receipt_totals') else pred

    # Check both fields
    is_btax_same = gold_totals.before_tax_total == pred_totals.before_tax_total
    is_atax_same = gold_totals.after_tax_total == pred_totals.after_tax_total

    # Calculate score
    score = float(is_btax_same and is_atax_same)

    # If no specific predictor feedback requested, return just the score
    if pred_name is None:
        return score

    # Generate detailed feedback for the predictor
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
        feedback = "Both totals extracted correctly! Great job identifying the subtotal and final total."
    else:
        feedback = " ".join(feedback_parts)
        feedback += " Tip: Tax is typically 8-10% of subtotal. Use this to validate your extraction."

    return dspy.Prediction(score=score, feedback=feedback)


# ============================================================================
# PART 3: Helper Functions
# ============================================================================

def resize_image_for_llm(img: Image.Image, max_width: int = 1024, max_height: int = 1024) -> Image.Image:
    """
    Resize image to fit within max dimensions while maintaining aspect ratio.
    This reduces context length for LLM processing.

    Args:
        img: PIL Image
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels

    Returns:
        Resized PIL Image
    """
    # Get current dimensions
    width, height = img.size

    # Calculate scaling factor
    scale = min(max_width / width, max_height / height, 1.0)

    # Only resize if image is larger than max dimensions
    if scale < 1.0:
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return img


def load_and_resize_image(path: str, max_width: int = 512, max_height: int = 512):
    """
    Load image from file and resize it for LLM processing.
    Returns a dspy.Image object.

    Args:
        path: Path to image file
        max_width: Maximum width in pixels (default 512 for Groq)
        max_height: Maximum height in pixels (default 512 for Groq)

    Returns:
        dspy.Image object with resized image
    """
    # Load as PIL Image first
    pil_img = Image.open(path)

    # Resize aggressively for Groq's smaller context window
    pil_img = resize_image_for_llm(pil_img, max_width, max_height)

    # Convert to base64 with lower quality
    buf = io.BytesIO()
    pil_img.convert("RGB").save(buf, format="JPEG", quality=60)
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Create dspy.Image from base64
    return dspy.Image(url=f"data:image/jpeg;base64,{b64}")


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

    # Resize image to reduce context length (512x512 for Groq)
    img = resize_image_for_llm(img, max_width=512, max_height=512)

    # Convert image to base64 with lower quality
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=60)
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Prepare messages
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        ]
    }]

    # Call LLM (using Gemini 2.0 directly for better OCR support)
    response = litellm.completion(
        model="gemini/gemini-2.0-flash",
        messages=messages,
        temperature=0,
        api_key=os.environ.get("GEMINI_API_KEY")
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
    Extract the after-tax total and the before-tax total from the receipt.
    """
    receipt_image: dspy.Image = dspy.InputField(
        desc="Receipt image to extract totals from"
    )
    receipt_totals: ReceiptTotals = dspy.OutputField(
        desc="Before-tax and after-tax totals"
    )


def create_training_data(test_mode=False):
    """
    Create DSPy training dataset.
    Based on cell 54 from prompt_optimization.ipynb.

    Args:
        test_mode: If True, use only 4 receipts for quick testing
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

    # Use only first 4 receipts in test mode
    if test_mode:
        goldset = goldset[:4]
        print(f"  ⚠ TEST MODE: Using only {len(goldset)} receipts for quick testing")

    # Convert to DSPy Examples (from cell 54)
    evalset = []
    for item in goldset:
        try:
            # Load and resize image to reduce context length (512x512 for Groq)
            img = load_and_resize_image(item["receipt_path"], max_width=512, max_height=512)
        except Exception as e:
            print(f"Warning: Could not load {item['receipt_path']}: {e}, skipping...")
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


def run_gepa_optimization(test_mode=False, delay_seconds=3):
    """
    Run GEPA optimization on receipt extraction.

    Args:
        test_mode: If True, use only 4 receipts for quick testing
        delay_seconds: Delay between API calls to avoid rate limits (default: 3)

    This function:
    1. Sets up student and reflection LLMs
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

    # Configure rate limiting
    import time
    original_completion = litellm.completion
    def rate_limited_completion(*args, **kwargs):
        time.sleep(delay_seconds)
        return original_completion(*args, **kwargs)
    litellm.completion = rate_limited_completion

    # Step 1: Set up LLMs (from cell 42)
    print("[1/7] Setting up language models...")
    if test_mode:
        print(f"  ⚠ TEST MODE: Using only 4 receipts")
    print(f"  Rate limiting: {delay_seconds}s delay between API calls")
    # Using Gemini 2.0 Flash directly - excellent vision + 1M context
    student_lm = dspy.LM(
        model="gemini/gemini-2.0-flash-exp",
        api_key=os.environ.get("GEMINI_API_KEY")
    )

    # For GEPA optimization - using same model for reflection
    reflection_lm = dspy.LM(
        model="gemini/gemini-2.0-flash-exp",
        api_key=os.environ.get("GEMINI_API_KEY")
    )
    print("  ✓ Student model: Gemini 2.0 Flash")
    print("  ✓ Reflection model: Gemini 2.0 Flash")
    print("  ✓ Context window: 1M tokens (no size issues!)")

    # Step 2: Create training data (from cell 54)
    print("\n[2/7] Loading training data...")
    print("  Loading and optimizing receipt images...")
    evalset, goldset = create_training_data(test_mode=test_mode)
    print(f"  ✓ Loaded {len(evalset)} receipt examples (512x512, 60% quality)")

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

    optimizer = dspy.GEPA(
        metric=metric_with_feedback,      # Our 5-parameter metric
        auto="light",                     # light/medium/heavy
        num_threads=1,                    # Sequential to avoid rate limits
        reflection_minibatch_size=2,      # Smaller batches
        reflection_lm=reflection_lm,      # Gemini for optimization
        track_stats=True                  # Log progress
    )
    print("  ✓ GEPA optimizer configured")
    print("    - Auto level: light (slower but avoids rate limits)")
    print("    - Threads: 1 (sequential processing)")
    print("    - Minibatch size: 2")
    print("    - Reflection LM: Gemini 2.0 Flash")

    # Step 7: Run optimization (from cell 58)
    print("\n[7/7] Running GEPA optimization...")
    print("  This will take 5-15 minutes...")
    print("  GEPA process:")
    print("    1. Run baseline on training examples")
    print("    2. Identify failures and collect feedback")
    print("    3. Llama analyzes failures in natural language")
    print("    4. Propose improved prompts")
    print("    5. Test candidates and maintain Pareto frontier")
    print("    6. Combine complementary lessons")
    print()

    try:
        dprogram_optimized = optimizer.compile(
            student=dprogram,
            trainset=trainset,
            valset=valset if valset else None
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
    if "GEMINI_API_KEY" not in os.environ:
        print("⚠ Error: GEMINI_API_KEY not set (required)")
        print("  Set with: export GEMINI_API_KEY='your-key'")
        exit(1)

    # Test mode configuration
    TEST_MODE = False  # Set to False for full 12-receipt optimization
    DELAY_SECONDS = 10  # Increased delay for all 12 receipts to avoid rate limits

    try:
        dprogram_optimized, table = run_gepa_optimization(
            test_mode=TEST_MODE,
            delay_seconds=DELAY_SECONDS
        )

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
