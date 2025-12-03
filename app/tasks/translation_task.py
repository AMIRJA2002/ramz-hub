"""Celery task for translating unprocessed articles"""
from app.celery_app import celery_app
from app.models.crawl_result import CrawlResult
from app.models.translation import Translation
from app.translation.translator import Translator
from app.tasks.helpers import run_async
from datetime import datetime, timezone
import traceback
import json
import asyncio


@celery_app.task(name="app.celery_app.translate_unprocessed_articles", bind=True)
def translate_unprocessed_articles(self):
    """Celery task to translate unprocessed articles"""
    print("=" * 60)
    print(f"[Translation Task] ===== STARTING TRANSLATION TASK =====")
    print(f"[Translation Task] Task ID: {self.request.id}")
    print("=" * 60)
    
    async def _translate_articles():
        try:
            # Find unprocessed articles (limit to 10 at a time to avoid overload)
            unprocessed_articles = await CrawlResult.find(
                CrawlResult.is_processed == False
            ).limit(10).to_list()
            
            if not unprocessed_articles:
                print("[Translation Task] No unprocessed articles found")
                return {
                    "processed": 0,
                    "skipped": 0,
                    "errors": 0,
                    "message": "No unprocessed articles"
                }
            
            print(f"[Translation Task] Found {len(unprocessed_articles)} unprocessed articles")
            
            processed_count = 0
            skipped_count = 0
            error_count = 0
            
            for article in unprocessed_articles:
                try:
                    # Check if article has required fields
                    if not article.title or not article.content:
                        print(f"[Translation Task] Skipping article {article.id} - missing title or content")
                        article.is_processed = True  # Mark as processed even if skipped
                        await article.save()
                        skipped_count += 1
                        continue
                    
                    # Check if translation already exists
                    existing_translation = await Translation.find_one(
                        Translation.article_id == str(article.id)
                    )
                    
                    if existing_translation:
                        print(f"[Translation Task] Translation already exists for article {article.id}")
                        article.is_processed = True
                        await article.save()
                        skipped_count += 1
                        continue
                    
                    # Translate article (run sync translator in thread pool)
                    print(f"[Translation Task] Translating article {article.id}: {article.title[:50]}...")
                    
                    # Run sync translator in executor
                    loop = asyncio.get_event_loop()
                    translator = Translator(article=article)
                    translation_json = await loop.run_in_executor(None, translator.translate)
                    
                    # Parse translation result
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
                    
                    # Mark article as processed
                    article.is_processed = True
                    await article.save()
                    
                    processed_count += 1
                    print(f"[Translation Task] ✓ Translated article {article.id}")
                    
                except json.JSONDecodeError as e:
                    print(f"[Translation Task] ✗ JSON decode error for article {article.id}: {str(e)}")
                    error_count += 1
                    # Don't mark as processed if translation failed
                    
                except Exception as e:
                    print(f"[Translation Task] ✗ Error translating article {article.id}: {str(e)}")
                    traceback.print_exc()
                    error_count += 1
                    # Don't mark as processed if translation failed
            
            result = {
                "processed": processed_count,
                "skipped": skipped_count,
                "errors": error_count,
                "total_found": len(unprocessed_articles)
            }
            
            print(f"[Translation Task] Completed: {result}")
            return result
            
        except Exception as e:
            print(f"[Translation Task] ERROR in translation task: {str(e)}")
            traceback.print_exc()
            raise
    
    try:
        result = run_async(_translate_articles())
        print("=" * 60)
        print(f"[Translation Task] ===== TASK COMPLETED SUCCESSFULLY =====")
        print("=" * 60)
        return result
    except Exception as e:
        print("=" * 60)
        print(f"[Translation Task] ===== TASK FAILED =====")
        print(f"[Translation Task] Error: {str(e)}")
        print("=" * 60)
        traceback.print_exc()
        raise

