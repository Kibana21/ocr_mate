"""
Optimization Configuration Models

Controls how GEPA optimization runs, including LLM selection,
rate limiting, and optimization parameters.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Language model configuration"""
    provider: Literal["gemini", "openai", "anthropic", "openrouter", "groq"] = "gemini"
    model_name: str = Field(..., description="Model identifier (e.g., 'gemini-2.0-flash-exp')")
    api_key: str = Field(..., description="API key for the provider")
    temperature: float = Field(default=0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens in response")


class ImageProcessingConfig(BaseModel):
    """Image preprocessing configuration"""
    max_width: int = Field(default=512, description="Max image width in pixels")
    max_height: int = Field(default=512, description="Max image height in pixels")
    jpeg_quality: int = Field(default=60, description="JPEG compression quality (1-100)")


class GEPAConfig(BaseModel):
    """GEPA optimizer configuration"""
    auto: Literal["light", "medium", "heavy"] = Field(
        default="light",
        description="Optimization level (light=fast, heavy=thorough)"
    )
    num_threads: int = Field(
        default=1,
        description="Number of parallel threads (1=sequential, avoids rate limits)"
    )
    reflection_minibatch_size: int = Field(
        default=2,
        description="Examples per reflection batch"
    )
    track_stats: bool = Field(
        default=True,
        description="Track detailed statistics during optimization"
    )


class OCRGroundingConfig(BaseModel):
    """OCR grounding configuration for enhanced extraction"""
    enabled: bool = Field(
        default=True,  # RECOMMENDED: Enable by default
        description="Use OCR text alongside image for better accuracy"
    )
    azure_endpoint: Optional[str] = Field(
        default=None,
        description="Azure Document Intelligence endpoint (from .env if None)"
    )
    azure_api_key: Optional[str] = Field(
        default=None,
        description="Azure Document Intelligence API key (from .env if None)"
    )
    use_native_markdown: bool = Field(
        default=True,
        description="Use Azure's native markdown output (RECOMMENDED)"
    )


class OptimizationConfig(BaseModel):
    """Complete optimization configuration"""
    # LLM configuration
    student_llm: LLMConfig = Field(..., description="LLM for inference (student)")
    reflection_llm: LLMConfig = Field(..., description="LLM for GEPA reflection")

    # GEPA configuration
    gepa: GEPAConfig = Field(default_factory=GEPAConfig)

    # Image processing
    image_processing: ImageProcessingConfig = Field(default_factory=ImageProcessingConfig)

    # OCR grounding (NEW - RECOMMENDED)
    ocr_grounding: OCRGroundingConfig = Field(
        default_factory=OCRGroundingConfig,
        description="OCR grounding for improved accuracy"
    )

    # Rate limiting
    delay_seconds: float = Field(
        default=5.0,
        description="Delay between API calls to avoid rate limits"
    )

    # Testing
    test_mode: bool = Field(
        default=False,
        description="If True, use only first 4 examples for quick testing"
    )

    # Training/validation split
    train_val_split: float = Field(
        default=0.8,
        description="Fraction of data for training (rest for validation)"
    )


# Example usage:
if __name__ == "__main__":
    import os

    # Example: Gemini configuration (like your current setup)
    config = OptimizationConfig(
        student_llm=LLMConfig(
            provider="gemini",
            model_name="gemini-2.0-flash-exp",
            api_key=os.getenv("GEMINI_API_KEY", "your-key-here")
        ),
        reflection_llm=LLMConfig(
            provider="gemini",
            model_name="gemini-2.0-flash-exp",
            api_key=os.getenv("GEMINI_API_KEY", "your-key-here")
        ),
        gepa=GEPAConfig(
            auto="light",
            num_threads=1,
            reflection_minibatch_size=2
        ),
        delay_seconds=10.0,
        test_mode=True  # Start with test mode
    )

    print(config.model_dump_json(indent=2))
