from pydantic import BaseModel, Field
from typing import Optional


class BaseAgentContract(BaseModel):
    """
    Base contract for all agent communications in the SentinelCell framework.
    """

    sender: str = Field(..., description="ID of the sending agent")
    receiver: str = Field(..., description="ID of the receiving agent")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the message")
    payload: dict = Field(..., description="Actual data payload")
    signature: Optional[str] = Field(
        None, description="Optional security signature to ensure compliance"
    )


class StatusContract(BaseModel):
    """
    Example specific contract for status updates.
    """

    status: str = Field(..., description="Status string, e.g. 'ok', 'error'")
    message: str = Field(..., description="Accompanying message")
