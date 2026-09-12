from pydantic import BaseModel, Field, field_validator


class AIProcessingResult(BaseModel):
    """
    Structured output contract for AI memory processing.
    
    This model represents the validated result returned by OpenAI Structured Outputs
    when processing a memory. It will be used to update the memory with:
    - summary: concise summary of the memory content
    - topics: list of topic strings extracted from the content
    - entities: list of entity strings extracted from the content
    """
    summary: str = Field(
        ..., 
        min_length=1, 
        max_length=500,
        description="Concise summary of the memory content"
    )
    topics: list[str] = Field(
        default_factory=list,
        description="List of topic strings extracted from the memory"
    )
    entities: list[str] = Field(
        default_factory=list,
        description="List of entity strings extracted from the memory"
    )

    @field_validator("topics", "entities", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("Must be a list")
        return v

    @field_validator("summary")
    @classmethod
    def summary_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Summary cannot be empty")
        return v.strip()