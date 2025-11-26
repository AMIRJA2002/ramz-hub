# Translation System Setup

## Overview
The translation system automatically translates crawled articles from English to Persian using Google's Gemini AI model.

## Components Created

### 1. Database Model (`app/models/translation.py`)
- `Translation` - Beanie document model for storing translations
- Fields: article_id, original_title, translated_title, translated_summary, source_site, translation_timestamp
- Indexed on: article_id, source_site, translation_timestamp

### 2. Pydantic Schemas (`app/models/schemas/translation_schema.py`)
- `TranslationResponse` - Schema for Gemini API response
- `TranslationCreate` - Schema for creating translations
- `TranslationOut` - Schema for translation output

### 3. Celery Task (`app/tasks/translation_tasks.py`)
- `translate_article_task` - Async Celery task that:
  - Runs in the `translator` queue
  - Fetches article from database
  - Calls Translator class to translate
  - Saves translation to database
  - Has retry logic (3 retries, exponential backoff)

### 4. Integration
- Updated `app/services/crawler_service.py` to automatically trigger translation task when a new article is saved
- Updated `app/celery_app.py` to include translation tasks and configure the translator queue
- Updated `app/database.py` to initialize Translation model with Beanie
- Fixed `app/translation/translator.py` to use `content` instead of `body` attribute

## How It Works

1. When a crawler saves a new article to the database
2. The crawler service automatically calls `translate_article_task.delay(article_id)`
3. The task is queued in the `translator` queue
4. A Celery worker picks up the task and:
   - Fetches the article
   - Checks if translation already exists (to avoid duplicates)
   - Calls the Translator class with the article
   - Parses the JSON response from Gemini
   - Saves the translation to the database

## Running the Translator Worker

To process translation tasks, start a Celery worker for the translator queue:

```bash
celery -A app.celery_app worker --loglevel=info -Q translator
```

Or run both default and translator queues:

```bash
celery -A app.celery_app worker --loglevel=info -Q celery,translator
```

## Configuration

Make sure `GEMINI_API_KEY` is set in your `.env` file for the translation to work.
