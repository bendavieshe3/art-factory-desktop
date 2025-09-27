"""
Mock factory for testing purposes.
"""

from typing import Dict, List, Any
from app.factories.base import (
    BaseProductFactory,
    ParameterSpec,
    ParameterType,
    GenerationResult,
)


class MockFactory(BaseProductFactory):
    """Mock factory for testing."""

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "test-model"

    def _load_parameter_specs(self) -> List[ParameterSpec]:
        """Load mock parameter specifications."""
        return [
            ParameterSpec(
                name="prompt",
                type=ParameterType.STRING,
                required=True,
                description="Text prompt for generation",
            ),
            ParameterSpec(
                name="steps",
                type=ParameterType.INTEGER,
                required=False,
                default=20,
                min_value=1,
                max_value=100,
                description="Number of inference steps",
            ),
            ParameterSpec(
                name="guidance_scale",
                type=ParameterType.FLOAT,
                required=False,
                default=7.5,
                min_value=1.0,
                max_value=20.0,
                description="Guidance scale for generation",
            ),
            ParameterSpec(
                name="scheduler",
                type=ParameterType.STRING,
                required=False,
                default="DPMSolverMultistep",
                choices=["DPMSolverMultistep", "DDIM", "PNDM"],
                description="Scheduler to use",
            ),
            ParameterSpec(
                name="enhance_quality",
                type=ParameterType.BOOLEAN,
                required=False,
                default=False,
                description="Enable quality enhancement",
            ),
            ParameterSpec(
                name="seed_list",
                type=ParameterType.ARRAY,
                required=False,
                description="List of seeds to use",
            ),
            ParameterSpec(
                name="metadata",
                type=ParameterType.OBJECT,
                required=False,
                description="Additional metadata",
            ),
        ]

    def _validate_provider_specific(self, params: Dict[str, Any], result):
        """Add mock provider-specific validation."""
        prompt = params.get("prompt", "")
        if prompt and len(prompt) > 1000:
            result.add_warning("prompt", "Very long prompts may be truncated")

        steps = params.get("steps")
        guidance = params.get("guidance_scale")
        if steps and guidance and steps < 10 and guidance > 15:
            result.add_warning(
                "steps", "Low steps with high guidance may produce poor results"
            )

    def create_actual_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert to mock API format."""
        api_params = {
            "input": {
                "prompt": params.get("prompt", ""),
                "num_inference_steps": params.get("steps", 20),
                "guidance_scale": params.get("guidance_scale", 7.5),
            }
        }

        if "scheduler" in params:
            api_params["input"]["scheduler"] = params["scheduler"]

        if "enhance_quality" in params:
            api_params["input"]["enhance"] = params["enhance_quality"]

        return api_params

    async def generate(self, params: Dict[str, Any]) -> GenerationResult:
        """Mock generation that always succeeds."""
        actual_params = self.create_actual_parameters(params)

        # Simulate successful generation
        return GenerationResult(
            success=True,
            products=[
                {
                    "type": "image",
                    "url": "https://mock.example.com/image1.jpg",
                    "width": 512,
                    "height": 512,
                    "format": "jpeg",
                }
            ],
            provider_request_id="mock-123",
            metadata={"actual_parameters": actual_params, "processing_time": 2.5},
        )


class MockFailingFactory(MockFactory):
    """Mock factory that always fails generation."""

    @property
    def model_name(self) -> str:
        return "failing-model"

    async def generate(self, params: Dict[str, Any]) -> GenerationResult:
        """Mock generation that always fails."""
        return GenerationResult(
            success=False,
            error_message="Mock generation failure",
            provider_request_id="mock-fail-123",
        )
