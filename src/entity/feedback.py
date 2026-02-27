from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class FeedbackBase(BaseModel):
    user_id: str = Field(description="User identifier")
    phone: str = Field(description="Contact phone number", example="13800138000")
    content: str = Field(description="Feedback content", min_length=5)
    is_processed: bool = Field(default=False, description="Processing status")

class FeedbackCreate(FeedbackBase):
    pass

class UpdateFeedbackRequest(BaseModel):
    is_read: Optional[bool] = Field(None, description="Read status")
    is_processed: Optional[bool] = Field(None, description="Processing status")
    admin_reply: Optional[str] = Field(None, description="Admin reply content")

class FeedbackResponse(FeedbackBase):
    id: int
    admin_reply: str | None = Field(description="Admin reply content", default=None)
    is_read: bool = Field(description="Whether user has read the reply", default=False)
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True  
    )