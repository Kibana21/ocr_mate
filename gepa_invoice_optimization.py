"""
GEPA Optimization for Invoice Extraction
==========================================

This script demonstrates how to use DSPy's GEPA optimizer to automatically
improve invoice extraction prompts based on ground truth examples.

Inspired by prompt_optimization.ipynb but adapted for invoice extraction.

Usage:
    python gepa_invoice_optimization.py

Requirements:
    pip install dspy-ai litellm pillow pixeltable pydantic
"""

import os
import io
import base64
import json
from pathlib import Path
from typing import Optional, Dict, List
from PIL import Image

import dspy
import pixeltable as pxt
from pixeltable import func
from pydantic import BaseModel, field_validator
import litellm


# ============================================================================
# PART 1: Data Models
# ============================================================================

class InvoiceData(BaseModel):
    """Pydantic model for structured invoice data."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    due_date: Optional[str] = None

    @field_validator('invoice_number', 'invoice_date', 'vendor_name',
                     'vendor_address', 'due_date', mode='before')
    @classmethod
    def extract_from_xml(cls, v):
        """Extract value from XML tags if present."""
        if v is None:
            return None
        if isinstance(v, str) and '<' in v:
            import re
            # Extract content between XML tags
            match = re.search(r'>([^<]+)<', v)
            if match:
                return match.group(1).strip()
        return v

    @field_validator('total_amount', 'tax_amount', mode='before')
    @classmethod
    def parse_currency(cls, v):
        """Parse currency values."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            import re
            # Remove currency symbols and commas
            clean = re.sub(r'[$,]', '', v.strip())
            # Extract from XML if present
            xml_match = re.search(r'>([^<]+)<', clean)
            if xml_match:
                clean = xml_match.group(1).strip()
            try:
                return float(clean)
            except ValueError:
                return None
        return None


# ============================================================================
# PART 2: Metric Function with Feedback (GEPA-compatible)
# ============================================================================

def invoice_metric_with_feedback(gold, pred, trace, pred_name, pred_trace):
    """
    GEPA-compatible metric function with 5 parameters.

    Args:
        gold: Ground truth example (dspy.Example with invoice_data)
        pred: Prediction from model (contains invoice_data)
        trace: Legacy parameter (may be None)
        pred_name: Name of the predictor being evaluated
        pred_trace: Detailed trace with reasoning steps

    Returns:
        dspy.Prediction(score=float, feedback=str)
    """
    # Extract ground truth and prediction
    gold_data = gold.invoice_data
    pred_data = pred.invoice_data

    # Define all fields to check
    fields = [
        'invoice_number', 'invoice_date', 'vendor_name',
        'vendor_address', 'total_amount', 'tax_amount', 'due_date'
    ]

    # Field-specific extraction hints
    field_hints = {
        'invoice_number': "Invoice number is typically in the top-right corner, labeled 'Invoice #', 'Invoice No', or 'Inv'. It often has a prefix like 'INV-'.",
        'invoice_date': "Invoice date is near the invoice number, labeled 'Date', 'Invoice Date', or 'Dated'. Format as YYYY-MM-DD.",
        'vendor_name': "Vendor name is the company name at the top of the document, usually in large or bold text.",
        'vendor_address': "Vendor address is below the vendor name, includes street, city, state, and ZIP code.",
        'total_amount': "Total amount is at the bottom, labeled 'Total', 'Amount Due', or 'Balance'. Don't confuse with subtotal.",
        'tax_amount': "Tax amount is usually above the total, labeled 'Tax', 'Sales Tax', or 'GST/HST'.",
        'due_date': "Due date is near the invoice date, labeled 'Due Date', 'Payment Due', or 'Pay By'. Format as YYYY-MM-DD."
    }

    # Calculate accuracy per field
    correct_fields = 0
    total_fields = len(fields)
    feedback_parts = []

    for field in fields:
        gold_value = getattr(gold_data, field, None)
        pred_value = getattr(pred_data, field, None)

        # Compare values
        if gold_value == pred_value:
            correct_fields += 1
        else:
            # Generate specific feedback for failed field
            feedback_part = (
                f"[{field}] Expected: '{gold_value}', Got: '{pred_value}'. "
                f"{field_hints.get(field, 'Check the document more carefully.')}"
            )
            feedback_parts.append(feedback_part)

    # Calculate overall score (0.0 to 1.0)
    score = correct_fields / total_fields

    # Combine feedback
    if feedback_parts:
        feedback = "\n".join(feedback_parts)
        feedback += f"\n\nOverall: {correct_fields}/{total_fields} fields correct ({score*100:.1f}%)"
    else:
        feedback = f"Perfect! All {total_fields} fields extracted correctly."

    return dspy.Prediction(score=score, feedback=feedback)


def simple_metric(gold, pred, trace, pred_name, pred_trace):
    """
    Simplified metric that just returns binary score (1.0 or 0.0).
    All fields must match exactly for score=1.0.
    """
    gold_data = gold.invoice_data
    pred_data = pred.invoice_data

    fields = ['invoice_number', 'invoice_date', 'vendor_name',
              'total_amount', 'tax_amount', 'due_date']

    all_match = all(
        getattr(gold_data, field, None) == getattr(pred_data, field, None)
        for field in fields
    )

    score = 1.0 if all_match else 0.0
    feedback = "All fields correct" if all_match else "Some fields incorrect"

    return dspy.Prediction(score=score, feedback=feedback)


# ============================================================================
# PART 3: LiteLLM-based Extraction Function (Baseline)
# ============================================================================

def extract_invoice_with_litellm(img: Image.Image, prompt: str, model: str = "groq/llama-4-scout-17b-16e-instruct") -> Dict:
    """
    Extract invoice data using LiteLLM (for baseline comparison).
    Similar to extract_totals() from prompt_optimization.ipynb.
    """
    # Convert image to base64
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=95)
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Prepare messages
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
            }
        ]
    }]

    # Call LLM
    response = litellm.completion(
        model=model,
        messages=messages,
        temperature=0
    )

    # Parse response
    response_text = response.choices[0]["message"]["content"]

    # Try to parse as InvoiceData
    try:
        invoice_data = InvoiceData.model_validate_json(response_text)
        return invoice_data.model_dump()
    except:
        # Fallback: try to extract from XML tags
        try:
            invoice_data = InvoiceData(
                invoice_number=response_text,
                invoice_date=response_text,
                vendor_name=response_text,
                vendor_address=response_text,
                total_amount=response_text,
                tax_amount=response_text,
                due_date=response_text
            )
            return invoice_data.model_dump()
        except:
            return {
                'invoice_number': None,
                'invoice_date': None,
                'vendor_name': None,
                'vendor_address': None,
                'total_amount': None,
                'tax_amount': None,
                'due_date': None
            }


# ============================================================================
# PART 4: Pixeltable Setup (Optional - for tracking versions)
# ============================================================================

def setup_pixeltable_tracking():
    """
    Set up Pixeltable for tracking optimization results.
    Similar to cells 9-20 in prompt_optimization.ipynb.
    """
    # Drop existing table if it exists
    pxt.drop_dir('invoice_optimization', force=True)
    pxt.create_dir('invoice_optimization')

    # Create table
    t = pxt.create_table('invoice_optimization.invoices', {
        'invoice_path': pxt.String,
        'invoice_image': pxt.Image
    })

    return t


def add_ground_truth_to_table(table, ground_truth_data: List[Dict]):
    """Add ground truth data to Pixeltable."""
    # Add ground truth column
    table.add_column(ground_truth=pxt.Json)

    # Insert data
    for item in ground_truth_data:
        table.insert(
            invoice_path=item['invoice_path'],
            invoice_image=item['invoice_path'],
            ground_truth=item['ground_truth']
        )

    return table


# ============================================================================
# PART 5: DSPy GEPA Optimization
# ============================================================================

class InvoiceExtraction(dspy.Signature):
    """Extract structured data from invoice image."""
    invoice_image: dspy.Image = dspy.InputField(
        desc="Invoice document image to extract data from"
    )
    invoice_data: InvoiceData = dspy.OutputField(
        desc="Structured invoice data with all fields"
    )


def create_training_data(data_dir: str = "images/invoices") -> tuple:
    """
    Create training and validation datasets.

    Args:
        data_dir: Directory containing invoice images

    Returns:
        (trainset, valset) tuple of dspy.Example lists
    """
    # Ground truth data
    # In a real scenario, this would come from your labeled examples
    ground_truth = [
        {
            'invoice_path': f'{data_dir}/invoice_001.jpg',
            'invoice_data': InvoiceData(
                invoice_number='INV-123456',
                invoice_date='2025-10-15',
                vendor_name='ACME Corporation',
                vendor_address='123 Business St, San Francisco, CA 94105',
                total_amount=1890.00,
                tax_amount=140.00,
                due_date='2025-11-15'
            )
        },
        {
            'invoice_path': f'{data_dir}/invoice_002.jpg',
            'invoice_data': InvoiceData(
                invoice_number='INV-234567',
                invoice_date='2025-10-16',
                vendor_name='TechCorp LLC',
                vendor_address='456 Tech Ave, New York, NY 10001',
                total_amount=2450.00,
                tax_amount=196.00,
                due_date='2025-11-16'
            )
        },
        {
            'invoice_path': f'{data_dir}/invoice_003.jpg',
            'invoice_data': InvoiceData(
                invoice_number='INV-345678',
                invoice_date='2025-10-17',
                vendor_name='Global Services Inc',
                vendor_address='789 Global Blvd, Austin, TX 78701',
                total_amount=3200.00,
                tax_amount=256.00,
                due_date='2025-11-17'
            )
        },
        {
            'invoice_path': f'{data_dir}/invoice_004.jpg',
            'invoice_data': InvoiceData(
                invoice_number='INV-456789',
                invoice_date='2025-10-18',
                vendor_name='Professional Solutions',
                vendor_address='321 Pro Lane, Seattle, WA 98101',
                total_amount=1750.00,
                tax_amount=140.00,
                due_date='2025-11-18'
            )
        },
        {
            'invoice_path': f'{data_dir}/invoice_005.jpg',
            'invoice_data': InvoiceData(
                invoice_number='INV-567890',
                invoice_date='2025-10-19',
                vendor_name='Enterprise Group',
                vendor_address='654 Enterprise Dr, Boston, MA 02101',
                total_amount=4100.00,
                tax_amount=328.00,
                due_date='2025-11-19'
            )
        },
    ]

    # Create DSPy examples
    all_examples = []
    for item in ground_truth:
        # Check if file exists, if not use placeholder
        if Path(item['invoice_path']).exists():
            img = dspy.Image.from_file(item['invoice_path'])
        else:
            print(f"Warning: {item['invoice_path']} not found, using placeholder")
            # Create a simple placeholder image for demonstration
            placeholder = Image.new('RGB', (800, 1000), color='white')
            img = dspy.Image.from_PIL(placeholder)

        example = dspy.Example(
            invoice_image=img,
            invoice_data=item['invoice_data']
        ).with_inputs('invoice_image')

        all_examples.append(example)

    # Split into train and validation (80/20)
    split_idx = int(len(all_examples) * 0.8)
    trainset = all_examples[:split_idx]
    valset = all_examples[split_idx:]

    return trainset, valset


def run_gepa_optimization():
    """
    Main function to run GEPA optimization on invoice extraction.
    Similar to cells 42-68 in prompt_optimization.ipynb.
    """
    print("=" * 80)
    print("GEPA OPTIMIZATION FOR INVOICE EXTRACTION")
    print("=" * 80)

    # Configure API keys (set these in your environment)
    if "GROQ_API_KEY" not in os.environ:
        print("\nWarning: GROQ_API_KEY not set. Using default (may fail).")
    if "OPENAI_API_KEY" not in os.environ:
        print("Warning: OPENAI_API_KEY not set. GEPA optimization may fail.")

    # Set up LLMs
    print("\n[1/6] Setting up language models...")
    student_lm = dspy.LM(
        model="groq/llama-4-scout-17b-16e-instruct",
        api_key=os.environ.get("GROQ_API_KEY")
    )

    reflection_lm = dspy.LM(
        model="openai/gpt-4o",
        api_key=os.environ.get("OPENAI_API_KEY")
    )

    # Create training data
    print("\n[2/6] Loading training data...")
    trainset, valset = create_training_data()
    print(f"  - Training set: {len(trainset)} examples")
    print(f"  - Validation set: {len(valset)} examples")

    # Create baseline program
    print("\n[3/6] Creating baseline DSPy program...")
    invoice_program = dspy.Predict(InvoiceExtraction)
    invoice_program.set_lm(student_lm)

    # Test baseline
    print("\n[4/6] Testing baseline program...")
    if trainset:
        test_result = invoice_program(invoice_image=trainset[0].invoice_image)
        print("  Baseline prediction sample:")
        print(f"    Invoice #: {test_result.invoice_data.invoice_number}")
        print(f"    Total: ${test_result.invoice_data.total_amount}")

    # Calculate baseline accuracy
    baseline_scores = []
    for example in trainset:
        pred = invoice_program(invoice_image=example.invoice_image)
        metric_result = invoice_metric_with_feedback(
            gold=example,
            pred=pred,
            trace=None,
            pred_name="baseline",
            pred_trace=None
        )
        baseline_scores.append(metric_result.score)

    baseline_accuracy = sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0
    print(f"  Baseline accuracy: {baseline_accuracy*100:.1f}%")

    # Create GEPA optimizer
    print("\n[5/6] Setting up GEPA optimizer...")
    optimizer = dspy.GEPA(
        metric=invoice_metric_with_feedback,  # 5-parameter metric
        auto="light",                         # light/medium/heavy
        num_threads=4,                        # Parallel evaluation
        reflection_minibatch_size=3,          # Examples per reflection
        reflection_lm=reflection_lm,          # GPT-4o for meta-optimization
        track_stats=True                      # Log progress
    )

    # Run optimization
    print("\n[6/6] Running GEPA optimization...")
    print("  This may take 5-15 minutes depending on 'auto' setting...")
    print("  GEPA will:")
    print("    1. Analyze failures in natural language")
    print("    2. Generate improved prompts")
    print("    3. Maintain Pareto frontier of diverse candidates")
    print("    4. Combine complementary lessons")
    print()

    try:
        optimized_program = optimizer.compile(
            student=invoice_program,
            trainset=trainset,
            valset=valset if valset else None
        )

        print("\n✓ Optimization complete!")

        # Test optimized program
        print("\n[7/6] Testing optimized program...")
        optimized_scores = []
        for example in trainset:
            pred = optimized_program(invoice_image=example.invoice_image)
            metric_result = invoice_metric_with_feedback(
                gold=example,
                pred=pred,
                trace=None,
                pred_name="optimized",
                pred_trace=None
            )
            optimized_scores.append(metric_result.score)

        optimized_accuracy = sum(optimized_scores) / len(optimized_scores) if optimized_scores else 0
        print(f"  Optimized accuracy: {optimized_accuracy*100:.1f}%")
        print(f"  Improvement: +{(optimized_accuracy - baseline_accuracy)*100:.1f}%")

        # Inspect optimized prompt
        print("\n[RESULTS] Optimized Prompt:")
        print("=" * 80)
        for name, predictor in optimized_program.named_predictors():
            print(f"\nPredictor: {name}")
            print(f"Instructions:\n{predictor.signature.instructions}")
            if hasattr(predictor, 'demos') and predictor.demos:
                print(f"Number of demonstrations: {len(predictor.demos)}")
        print("=" * 80)

        # Save optimized program
        output_path = "invoice_pipeline_gepa_optimized.json"
        optimized_program.save(output_path)
        print(f"\n✓ Optimized program saved to: {output_path}")

        return optimized_program

    except Exception as e:
        print(f"\n✗ Optimization failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure OPENAI_API_KEY is set for GEPA optimization")
        print("  2. Ensure GROQ_API_KEY is set for student model")
        print("  3. Check that invoice images exist in images/invoices/")
        print("  4. Verify internet connection for API calls")
        raise


# ============================================================================
# PART 6: Comparison with Manual Optimization (like cells 21-41)
# ============================================================================

def manual_prompt_optimization_example():
    """
    Example of manual iterative prompt optimization.
    Similar to the manual approach in cells 21-41 of prompt_optimization.ipynb.
    """
    print("\n" + "=" * 80)
    print("MANUAL PROMPT OPTIMIZATION (for comparison)")
    print("=" * 80)

    # Initial simple prompt
    initial_prompt = """
Extract the following information from the invoice image:
- Invoice Number
- Invoice Date
- Vendor Name
- Total Amount
- Tax Amount
- Due Date

Return the values in JSON format.
"""

    print("\nInitial Prompt:")
    print(initial_prompt)
    print("\n→ This would be tested on examples, failures collected")
    print("→ An LLM (GPT-4) would analyze failures and propose improvements")
    print("→ Process repeats 3-5 times")
    print("→ More manual work, but educational!")
    print("\nGEPA automates this entire process! 🚀")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GEPA Invoice Extraction Optimization")
    parser.add_argument("--mode", choices=["gepa", "manual", "both"], default="gepa",
                       help="Which optimization approach to demonstrate")
    parser.add_argument("--data-dir", default="images/invoices",
                       help="Directory containing invoice images")

    args = parser.parse_args()

    try:
        if args.mode in ["manual", "both"]:
            manual_prompt_optimization_example()

        if args.mode in ["gepa", "both"]:
            optimized_program = run_gepa_optimization()

            print("\n" + "=" * 80)
            print("SUCCESS! Your invoice extraction pipeline has been optimized.")
            print("=" * 80)
            print("\nNext steps:")
            print("  1. Test on new invoices using: optimized_program(invoice_image=img)")
            print("  2. Collect more ground truth examples to improve further")
            print("  3. Re-run optimization with additional examples")
            print("  4. Deploy to production when accuracy is satisfactory")
            print("\nFor OCR Mate integration:")
            print("  - Load: optimized_program = dspy.load('invoice_pipeline_gepa_optimized.json')")
            print("  - Use in API: result = optimized_program(invoice_image=image)")
            print("  - Track performance and re-optimize with user corrections")

    except KeyboardInterrupt:
        print("\n\nOptimization interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
