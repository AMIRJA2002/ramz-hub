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
        self.openrouter_model = openrouter_model or "google/gemini-2.5-pro"

    def _client(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        a = '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'
        return genai.Client(api_key=a)

    def _prompt(self, title: str, body: str):
        data: dict = {"title": title, "body": body}

        return f"""
    You will receive a JSON object containing an English 'title' and 'body' of a cryptocurrency-related article.

    Your tasks:

    1. Translate the 'title' into Persian and return it as a string.
    2. Translate the 'body' into Persian and highlight key points:
       - Keep it concise and clear.
       - Use tags or markers for important sections if relevant.
    3. Perform sentiment analysis on the article:
       - Provide a score from 1 to 5 (1 = very negative, 5 = very positive).
       - Include a brief explanation if needed.
    4. Identify mentioned cryptocurrencies:
       - Return a list of objects with 'name' and 'symbol' for each currency mentioned (e.g., "Bitcoin" -> "BTC").
    5. Explain briefly why this news is important in one or two sentences.
    6. Describe the potential impact of this news on the market in one or two sentences.
    7. Return ONLY a valid JSON object with the following keys:

    {{
      "title": "...",               # Persian translation of the title
      "body": "...",                # Persian translation of the body with highlighted key points
      "sentiment_score": 1,         # 1 to 5
      "tags": ["BTC", "ETH", ...],  # list of cryptocurrency symbols mentioned
      "importance": "...",          # why this news is important
      "market_impact": "..."        # impact on the market
    }}

    Input JSON:
    {json.dumps(data, ensure_ascii=False)}
    """

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
            json={
                "model": self.openrouter_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}  # forces JSON output
            },
            timeout=60
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        result = response.json()
        
        # Check for API errors
        if "error" in result:
            raise Exception(f"OpenRouter API error: {result['error']}")
        
        if "choices" not in result or len(result["choices"]) == 0:
            raise Exception(f"Invalid response from OpenRouter: {result}")
        
        return result["choices"][0]["message"]["content"]

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

    async def translate_and_save(self):
        """Translate article and save to Translation model"""
        existing = await Translation.find_one(
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
        await translation.insert()
        return translation
