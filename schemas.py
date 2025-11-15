"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# PakGPT News Engine Schemas

class NewsItem(BaseModel):
    """Normalized news document for a single story/language."""
    source: str = Field(..., description="News source identifier")
    title: str = Field(..., description="Article headline")
    url: str = Field(..., description="Canonical URL")
    published_at: Optional[datetime] = Field(None, description="Publication time")
    city: Optional[str] = Field(None, description="Primary city tag (e.g., Karachi, Lahore)")
    interests: List[str] = Field(default_factory=list, description="Tags like politics, economy, jobs, tech, sports")
    urgency: Literal["breaking", "important", "full"] = Field("full", description="User urgency level mapped for this item")

    # AI outputs
    language: Literal["en", "ur"] = Field("en", description="Language of generated summary")
    bullets: List[str] = Field(default_factory=list, description="Exactly 3 bullet points")
    impact: str = Field("", description="One-line impact statement")

    # Trust & verification
    fact_status: Literal["Verified", "Unconfirmed", "Rumour"] = Field("Unconfirmed")
    risk_score: Optional[int] = Field(0, ge=0, le=100, description="Risk score for rumours (0-100)")

    # Misc
    thumbnail: Optional[str] = Field(None, description="Image URL if available")
    source_id: Optional[str] = Field(None, description="Source-specific id or guid")

class Subscription(BaseModel):
    """User subscription preferences for daily digest and feed."""
    name: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    whatsapp: Optional[str] = Field(None, description="WhatsApp phone in international format")

    city: Optional[str] = Field(None)
    interests: List[str] = Field(default_factory=list)
    urgency: Literal["breaking", "important", "full"] = Field("important")
    language: Literal["en", "ur"] = Field("en")

    notifications: List[str] = Field(default_factory=lambda: ["app"], description="Any of ['app','email','whatsapp']")
