import json
import requests

from app.config import settings
from app.models.crawl_result import CrawlResult
from app.models.translation import Translation
from google import genai


class Translator:
    def __init__(self, article: CrawlResult, provider="openrouter", openrouter_model=None):
        """
        provider: "google" or "openrouter"
        openrouter_model: e.g. "amazon/nova-2-lite-v1:free"
        """
        self.article = article
        self.provider = provider
        self.openrouter_model = openrouter_model or "google/gemini-2.0-flash-exp:free"

    # ------------------- GOOGLE -------------------

    def _client(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        return genai.Client(api_key=settings.GEMINI_API_KEY)

    # ------------------- PROMPT -------------------

    def _prompt(self, title: str, body: str):
        data: dict = {"title": title, "body": body}

        return f"""
You will receive a JSON object containing an English 'title' and 'body'.

Your tasks:
1. Translate the 'title' into Persian.
2. Summarize the 'body' in Persian:
   - Remove redundant or repeated content.
   - Exclude anything unrelated to the main article.
   - Keep the summary concise, clear, and accurate.
3. Return ONLY a valid JSON object in this exact format:

{{
  "title": "...",
  "summary": "..."
}}

Input JSON:
{json.dumps(data, ensure_ascii=False)}
"""

    # ------------------- OPENROUTER -------------------

    def _call_openrouter_model(self, prompt: str):
        API_KEY = settings.OPENROUTER_API_KEY
        if not API_KEY:
            raise ValueError("OPENROUTER_API_KEY is not set")

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": self.openrouter_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}  # forces JSON output
            })
        )

        result = response.json()
        return result["choices"][0]["message"]["content"]

    # ------------------- GOOGLE -------------------

    def _call_model_google(self, client, prompt: str):
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
        ]

        response = client.models.generate_content(
            model=models_to_try[0],
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return response.text

    # ------------------- MAIN ENTRY -------------------

    def translate(self):
        title, body = self.article.title, self.article.content
        prompt = self._prompt(title=title, body=body)

        # Auto-switch between providers
        # if self.provider == "google":
        #     client = self._client()
        #     result = self._call_model_google(client, prompt)
        if self.provider == "openrouter":
            result = self._call_openrouter_model(prompt)
        else:
            raise ValueError("Invalid provider: choose 'google' or 'openrouter'")

        return result

    # ------------------- SAVE RESULT -------------------

    def translate_and_save(self):
        """Translate article and save to Translation model"""
        existing = Translation.find_one(
            Translation.article_id == str(self.article.id)
        )
        if existing:
            return existing

        translation_json = self.translate()
        translation_data = json.loads(translation_json)

        translation = Translation(
            article_id=str(self.article.id),
            original_title=self.article.title or '',
            translated_title=translation_data.get('title', ''),
            translated_summary=translation_data.get('summary', ''),
            source_site=self.article.source_site
        )
        translation.insert()
        return translation
