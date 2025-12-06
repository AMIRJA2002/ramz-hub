"""Celery task for translating unprocessed articles"""
from app.celery_app import celery_app
from app.models.crawl_result import CrawlResult
from app.models.translation import Translation
from app.translation.translator import Translator
from app.tasks.helpers import run_async
import json


@celery_app.task(name="app.celery_app.translate_unprocessed_articles", bind=True)
def translate_unprocessed_articles(self):
    """Celery task to translate unprocessed articles"""
    
    async def _translate():
        articles = await CrawlResult.find(CrawlResult.is_processed == False).limit(10).to_list()
        
        processed = 0
        skipped = 0
        errors = 0
        
        for article in articles:
            try:
                # Skip if missing title or content
                if not article.title or not article.content:
                    article.is_processed = True
                    await article.save()
                    skipped += 1
                    continue
                
                # Check if translation exists
                existing = await Translation.find_one(Translation.article_id == str(article.id))
                if existing:
                    article.is_processed = True
                    await article.save()
                    skipped += 1
                    continue
                
                # Translate
                translator = Translator(article)
                translation_json = translator.translate()
                translation_data = json.loads(translation_json)
                
                # Save translation
                translation = Translation(
                    article_id=str(article.id),
                    original_title=article.title or '',
                    translated_title=translation_data.get('title', ''),
                    translated_summary=translation_data.get('summary', ''),
                    source_site=article.source_site
                )
                await translation.insert()
                
                # Mark as processed
                article.is_processed = True
                await article.save()
                processed += 1
                
            except Exception as e:
                print(f"Error: {e}")
                errors += 1
        
        return {"processed": processed, "skipped": skipped, "errors": errors}
    
    return run_async(_translate())
