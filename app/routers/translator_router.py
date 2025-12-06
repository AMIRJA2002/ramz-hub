import json

from bson import ObjectId
from app.models.crawl_result import CrawlResult
from app.translation.translator import Translator
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/translate", tags=["translator"])


class TranslateRequest(BaseModel):
    article_id: str


@router.post('/translate')
async def translate_article(request: TranslateRequest):
    """Translate an article by its ID"""
    try:
        obj_id = ObjectId(request.article_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    article = await CrawlResult.get(obj_id)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    try:
        translator = Translator(article)
        data = translator.translate()
        return {'msg': str(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")
