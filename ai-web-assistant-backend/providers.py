from abc import ABC, abstractmethod
from typing import Dict, Optional
from openai import OpenAI
from anthropic import Anthropic
from config import Config

class AIProvider(ABC):
    @abstractmethod
    def ask_question(self, question: str, context: str, model: Optional[str] = None) -> Dict:
        pass

    def truncate_text(self, text: str, max_chars: int = 4000) -> str:
        """Truncate text to a maximum number of characters while trying to keep complete sentences."""
        if len(text) <= max_chars:
            return text
        
        truncated = text[:max_chars]
        last_period = truncated.rfind('.')
        last_question = truncated.rfind('?')
        last_exclamation = truncated.rfind('!')
        
        cut_point = max(last_period, last_question, last_exclamation)
        if cut_point > 0:
            return text[:cut_point + 1]
        return truncated + "..."

class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def ask_question(self, question: str, context: str, model: Optional[str] = None) -> Dict:
        try:
            truncated_context = self.truncate_text(context)
            response = self.client.chat.completions.create(
                model=model or Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant analyzing webpage content."},
                    {"role": "user", "content": f"Context: {truncated_context}\n\nQuestion: {question}"}
                ],
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE
            )
            return {"answer": response.choices[0].message.content}
        except Exception as e:
            return {"error": str(e)}

class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def ask_question(self, question: str, context: str, model: Optional[str] = None) -> Dict:
        try:
            truncated_context = self.truncate_text(context)
            message = self.client.messages.create(
                model=model or Config.CLAUDE_MODEL,
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE,
                system="You are a helpful assistant analyzing webpage content.",
                content=f"Context: {truncated_context}\n\nQuestion: {question}"
            )
            return {"answer": message.content[0].text}
        except Exception as e:
            return {"error": str(e)}

class AIProviderFactory:
    @staticmethod
    def create_provider(provider_type: str, api_key: str) -> Optional[AIProvider]:
        providers = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider
        }
        
        provider_class = providers.get(provider_type.lower())
        if provider_class:
            return provider_class(api_key)
        return None