import json

from app.config import settings
from app.models.crawl_result import CrawlResult
from app.models.translation import Translation
from google import genai


class Translator:
    def __init__(self, article: CrawlResult, ):
        self.article = article

    def _client(self):
        return genai.Client(api_key=settings.GEMINI_API_KEY)

    def _prompt(self, title: str, body: str):
        data: dict = {"title": title, "body": body}

        prompt = f"""
            You will receive JSON input containing an English title and body.

            Your task:
            1. Translate the title into Persian.
            2. Summarize the body in Persian, remove extra or repeated content, exclude sections unrelated to the main article, and remove the .
            3. Return a clean JSON output ONLY in this format:

            {{
              "title": "{title}",
              "summary": "..."
            }}

            Input JSON:
            {json.dumps(data, ensure_ascii=False)}
            """

        return prompt


    def _call_model(self, client, prompt):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                # "response_json_schema": Recipe.model_json_schema(),
            },
        )

        return response.text  # already JSON string

    def translate(self):
        title, body = self.article.title, self.article.content
        client = self._client()
        prompt = self._prompt(title=title, body=body)
        return self._call_model(client=client, prompt=prompt)
    
    def translate_and_save(self):
        """Translate article and save to Translation model"""
        # Check if translation already exists
        existing = Translation.find_one(
            Translation.article_id == str(self.article.id)
        ).run()
        
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
