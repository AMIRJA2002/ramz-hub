"""
Celery tasks for translation operations
"""
from celery import Task
from app.celery_app import celery_app
from app.database import connect_to_mongo, close_mongo_connection
from app.models.crawl_result import CrawlResult
from app.models.translation import Translation
from app.translation.translator import Translator
import asyncio
import logging
import json

logger = logging.getLogger(__name__)

#
# class AsyncTask(Task):
#     """Base task class that handles async operations"""
#
#     def __call__(self, *args, **kwargs):
#         """Execute async task in event loop"""
#         try:
#             # Try to get the current event loop
#             loop = asyncio.get_event_loop()
#             if loop.is_running():
#                 # If loop is running, create a new one
#                 loop = asyncio.new_event_loop()
#                 asyncio.set_event_loop(loop)
#                 try:
#                     return loop.run_until_complete(self.run_async(*args, **kwargs))
#                 finally:
#                     loop.close()
#             else:
#                 # Use existing loop if not running
#                 return loop.run_until_complete(self.run_async(*args, **kwargs))
#         except RuntimeError:
#             # No event loop exists, create a new one
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)
#             try:
#                 return loop.run_until_complete(self.run_async(*args, **kwargs))
#             finally:
#                 loop.close()
#
#     async def run_async(self, *args, **kwargs):
#         """Override this method in subclasses"""
#         raise NotImplementedError
#

@celery_app.task(
    bind=True,
    name='app.tasks.translation_tasks.translate_article_task',
    queue='translator',
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # 10 minutes max
    retry_jitter=True,
)

def translator_task(article_id: str):
    """
    Translate a specific article

    Args:
        article_id: ID of the CrawlResult to translate

    Returns:
        dict: Translation result with statistics
    """
    try:
        logger.info(f"Starting translation task for article {article_id}")

        # Connect to database
        connect_to_mongo()

        # Get the article
        article = CrawlResult.get(article_id)
        if not article:
            logger.error(f"Article {article_id} not found")
            return {
                'success': False,
                'error': 'Article not found',
                'article_id': article_id
            }

        # Check if translation already exists
        existing_translation = Translation.find_one(
            Translation.article_id == article_id
        )
        if existing_translation:
            logger.info(f"Translation already exists for article {article_id}")
            return {
                'success': True,
                'message': 'Translation already exists',
                'article_id': article_id,
                'translation_id': str(existing_translation.id)
            }

        # Translate the article
        translator = Translator(article=article)
        translation_json = translator.translate()

        # Parse the JSON response
        translation_data = json.loads(translation_json)

        # Create translation record
        translation = Translation(
            article_id=article_id,
            original_title=article.title or '',
            translated_title=translation_data.get('title', ''),
            translated_summary=translation_data.get('summary', ''),
            source_site=article.source_site
        )

        translation.insert()

        logger.info(f"Successfully translated article {article_id}")

        return {
            'success': True,
            'article_id': article_id,
            'translation_id': str(translation.id),
            'translated_title': translation.translated_title[:100]
        }

    except Exception as exc:
        logger.error(f"Error translating article {article_id}: {str(exc)}")
        # Re-raise to trigger retry
        raise

    finally:
        # Clean up database connection
        try:
            close_mongo_connection()
        except:
            pass


# Create task instance
translate_article_task = translator_task()
