import json

from app.config import settings
from app.models.crawl_result import CrawlResult
from app.models.translation import Translation
from google import genai


class Translator:
    def __init__(self, article: CrawlResult, ):
        self.article = article

    def _client(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        return genai.Client(api_key=settings.GEMINI_API_KEY)

    def _prompt(self, title: str, body: str):
        data: dict = {"title": title, "body": body}

        prompt = f"""
You will receive JSON input containing an English title and body.

Your task:
1. Translate the title into Persian.
2. Summarize the body in Persian, remove extra or repeated content, exclude sections unrelated to the main article.
3. Return a clean JSON output ONLY in this format:

{{
  "title": "...",
  "summary": "..."
}}

Input JSON:
{json.dumps(data, ensure_ascii=False)}
"""

        return prompt


    def _call_model(self, client, prompt):
        """Call Gemini API with fallback models"""
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
        ]
        
        last_error = None
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                    },
                )
                return response.text  # already JSON string
            except Exception as e:
                last_error = e
                # If it's a 403 or model not found, try next model
                error_str = str(e)
                if "403" not in error_str and "not found" not in error_str.lower():
                    # If it's a different error, raise it immediately
                    raise
                # Otherwise, continue to next model
                continue
        
        # If all models failed, raise the last error
        raise Exception(f"All models failed. Last error: {last_error}")

    def translate(self):
        title, body = self.article.title, self.article.content
        client = self._client()
        prompt = self._prompt(title=title, body=body)
        result = self._call_model(client=client, prompt=prompt)
        return result
    
    def translate_and_save(self):
        """Translate article and save to Translation model"""
        # Check if translation already exists
        existing = Translation.find_one(
            Translation.article_id == str(self.article.id)
        )
        
        if existing:
            return existing
        
        # Translate
        translation_json = self.translate()
        translation_data = json.loads(translation_json)
        
        # Save to database
        translation = Translation(
            article_id=str(self.article.id),
            original_title=self.article.title or '',
            translated_title=translation_data.get('title', ''),
            translated_summary=translation_data.get('summary', ''),
            source_site=self.article.source_site
        )
        translation.insert()
        
        return translation
