from pydantic import BaseModel, Field
from typing import Optional

# AI-Powered Generators
class BioGeneratorRequest(BaseModel):
    niche: str = Field(..., description="E.g., Tech Influencer, Food Blogger, Entrepreneur")
    tone: str = Field("Creative", description="E.g., Professional, Funny, Creative, Minimalist")
    key_details: Optional[str] = Field(None, description="Specific details to include (e.g., 'Coffee addict, Based in NY')")

class UsernameGeneratorRequest(BaseModel):
    base_name: str = Field(..., description="Your actual name or base word")
    niche_or_interests: Optional[str] = Field(None, description="E.g., Gaming, Photography, Coding")
    vibe: str = Field("Aesthetic", description="E.g., Aesthetic, Professional, Edgy, Cute")

class CaptionGeneratorRequest(BaseModel):
    post_description: str = Field(..., description="Describe what the post/photo is about")
    tone: str = Field("Engaging", description="E.g., Engaging, Funny, Inspirational, Short")
    include_emojis: bool = Field(True, description="Whether to include emojis in the caption")

class HashtagGeneratorRequest(BaseModel):
    topic: str = Field(..., description="The main topic of your post")
    count: int = Field(15, description="Number of hashtags to generate (max 30)")

# Logic-Based Tools
class TextRequest(BaseModel):
    text: str = Field(..., description="The input text to process")

class FancyTextRequest(BaseModel):
    text: str = Field(..., description="The input text to make fancy")
