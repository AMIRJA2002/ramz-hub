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
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
        ]
        
        response = client.models.generate_content(
            model=models_to_try[0],
            contents=prompt,
            config={
                "response_mime_type": "application/json",
            },
        )
        return response.text

    def translate(self):
        title, body = self.article.title, self.article.content
        client = self._client()
        prompt = self._prompt(title=title, body=body)
        result = self._call_model(client=client, prompt=prompt)
        print(result, 400 * '*')
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
