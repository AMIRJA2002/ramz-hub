from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TranslationResponse(BaseModel):
    """Schema for translation API response"""
    title: str = Field(..., description="Translated title in Persian")
    summary: str = Field(..., description="Translated and summarized body in Persian")


class TranslationCreate(BaseModel):
    """Schema for creating a translation"""
    article_id: str = Field(..., description="ID of the article to translate")


class TranslationOut(BaseModel):
    """Schema for translation output"""
    id: str
    article_id: str
    original_title: str
    translated_title: str
    translated_summary: str
    source_site: str
    translation_timestamp: datetime
    
    class Config:
        from_attributes = True
