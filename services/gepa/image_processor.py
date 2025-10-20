"""
Image Processing Utilities for GEPA Optimization

Resizes and compresses images to reduce context length and API costs.
Extracted from gepa_receipt_optimization.py
"""

import io
import base64
from PIL import Image
import dspy
from typing import Optional


def resize_image_for_llm(
    img: Image.Image,
    max_width: int = 1024,
    max_height: int = 1024
) -> Image.Image:
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


def load_and_resize_image(
    path: str,
    max_width: int = 512,
    max_height: int = 512,
    jpeg_quality: int = 60
) -> dspy.Image:
    """
    Load image from file and resize it for LLM processing.
    Returns a dspy.Image object.

    Args:
        path: Path to image file
        max_width: Maximum width in pixels (default 512 for Groq/budget LLMs)
        max_height: Maximum height in pixels (default 512)
        jpeg_quality: JPEG compression quality 1-100 (default 60)

    Returns:
        dspy.Image object with resized and compressed image
    """
    # Load as PIL Image first
    pil_img = Image.open(path)

    # Resize
    pil_img = resize_image_for_llm(pil_img, max_width, max_height)

    # Convert to base64 with compression
    buf = io.BytesIO()
    pil_img.convert("RGB").save(buf, format="JPEG", quality=jpeg_quality)
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Create dspy.Image from base64
    return dspy.Image(url=f"data:image/jpeg;base64,{b64}")


def pil_to_dspy_image(
    pil_img: Image.Image,
    max_width: int = 512,
    max_height: int = 512,
    jpeg_quality: int = 60
) -> dspy.Image:
    """
    Convert PIL Image to dspy.Image with resizing and compression.

    Args:
        pil_img: PIL Image object
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        jpeg_quality: JPEG compression quality 1-100

    Returns:
        dspy.Image object
    """
    # Resize
    pil_img = resize_image_for_llm(pil_img, max_width, max_height)

    # Convert to base64 with compression
    buf = io.BytesIO()
    pil_img.convert("RGB").save(buf, format="JPEG", quality=jpeg_quality)
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Create dspy.Image from base64
    return dspy.Image(url=f"data:image/jpeg;base64,{b64}")


# Example usage
if __name__ == "__main__":
    # Test image loading
    test_image_path = "images/receipts/IMG_2171.jpg"

    try:
        dspy_img = load_and_resize_image(
            test_image_path,
            max_width=512,
            max_height=512,
            jpeg_quality=60
        )
        print(f"✓ Successfully loaded and processed image")
        print(f"  Image data length: {len(dspy_img.url)} chars")
    except FileNotFoundError:
        print(f"⚠ Test image not found: {test_image_path}")
        print("  This is expected if running outside the project directory")
