"""
Pydantic schemas for application health and status checks.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Overall service status")
    app_name: str = Field(description="Name of the application")
    environment: str = Field(description="Active environment")
    version: str = Field(default="0.2.0", description="API version")
    database: str = Field(default="connected", description="Database connectivity status")
