from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class MechanicValidationResult(BaseModel):
    success: bool = Field(..., description="Whether the mechanic requirements were satisfied")
    score: float = Field(0.0, description="Calculated final or peak score")
    max_score_reached: float = Field(0.0, description="Highest score achieved during the attempt")
    message: str = Field(..., description="Human-readable explanation of the result")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed diagnostic metrics")


class BaseMechanicValidator(ABC):
    @abstractmethod
    def validate(
        self,
        mechanic_params: Dict[str, Any],
        submission_data: Optional[Dict[str, Any]] = None,
    ) -> MechanicValidationResult:
        """Validate whether the user's mechanic submission satisfies the parameters."""
        pass
