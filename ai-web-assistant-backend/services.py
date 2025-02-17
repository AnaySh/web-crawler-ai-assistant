from typing import Optional, List, Dict
import openai
from models import APIKey, QAPair, Provider, Model
from db import db_session
from config import Config

class OpenAIService:
    @staticmethod
    def get_api_key() -> Optional[str]:
        api_key = APIKey.query.filter_by(is_valid=True).first()
        return api_key.key if api_key else None

    @staticmethod
    def truncate_text(text: str, max_chars: int = 4000) -> str:
        """Truncate text to a maximum number of characters while trying to keep complete sentences."""
        if len(text) <= max_chars:
            return text
        
        # Try to find the last sentence boundary before max_chars
        truncated = text[:max_chars]
        last_period = truncated.rfind('.')
        last_question = truncated.rfind('?')
        last_exclamation = truncated.rfind('!')
        
        # Find the last sentence boundary
        cut_point = max(last_period, last_question, last_exclamation)
        if cut_point > 0:
            return text[:cut_point + 1]
        return truncated + "..."

    @staticmethod
    async def ask_question(question: str, context: str, provider: str = "openai", model: str = None) -> Dict:
        # Get the appropriate API key
        query = APIKey.query.filter_by(provider=provider, is_valid=True)
        api_key = query.first()
        
        if not api_key:
            return {"error": f"No valid API key found for provider: {provider}"}

        # Truncate context if too long
        truncated_context = OpenAIService.truncate_text(context)
        
        try:
            if provider == "openai":
                client = openai.OpenAI(api_key=api_key.key)
                response = await client.chat.completions.create(
                    model=model or api_key.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant analyzing webpage content."},
                        {"role": "user", "content": f"Context: {truncated_context}\n\nQuestion: {question}"}
                    ],
                    max_tokens=Config.MAX_TOKENS,
                    temperature=Config.TEMPERATURE
                )
                return {"answer": response.choices[0].message.content}
            elif provider == "anthropic":
                # Add Anthropic API implementation here
                # You would need to install and import the Anthropic client
                return {"error": "Anthropic API implementation pending"}
            else:
                return {"error": f"Unsupported provider: {provider}"}
        except Exception as e:
            return {"error": str(e)}

class DatabaseService:
    @staticmethod
    def save_qa_pair(webpage_url: str, question: str, answer: str, context: Optional[str] = None, created_by: Optional[str] = None) -> Dict:
        try:
            qa_pair = QAPair(
                webpage_url=webpage_url,
                question=question,
                answer=answer,
                context=context,
                created_by=created_by
            )
            db_session.add(qa_pair)
            db_session.commit()
            return {"success": True, "id": qa_pair.id}
        except Exception as e:
            db_session.rollback()
            return {"error": str(e)}

    @staticmethod
    def get_qa_pairs(webpage_url: str) -> List[Dict]:
        try:
            qa_pairs = QAPair.query.filter_by(webpage_url=webpage_url).all()
            return [{
                "id": qa.id,
                "question": qa.question,
                "answer": qa.answer,
                "created_at": qa.created_at.isoformat()
            } for qa in qa_pairs]
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def delete_qa_pair(qa_id: int) -> Dict:
        try:
            qa_pair = QAPair.query.get(qa_id)
            if not qa_pair:
                return {"error": "QA pair not found"}
            db_session.delete(qa_pair)
            db_session.commit()
            return {"success": True}
        except Exception as e:
            db_session.rollback()
            return {"error": str(e)}

    @staticmethod
    def update_api_key(key: str, provider: str, model: str, user_id: str = None) -> Dict:
        try:
            # Validate provider and model
            if provider not in [p.value for p in Provider]:
                return {"error": f"Invalid provider. Must be one of: {[p.value for p in Provider]}"}
            if model not in [m.value for m in Model]:
                return {"error": f"Invalid model. Must be one of: {[m.value for m in Model]}"}
            
            # Invalidate existing keys for this user and provider if user_id is provided
            if user_id:
                APIKey.query.filter_by(user_id=user_id, provider=provider).update({"is_valid": False})
            else:
                # If no user_id, invalidate all keys without user_id for this provider
                APIKey.query.filter_by(user_id=None, provider=provider).update({"is_valid": False})
            
            # Create new key
            api_key = APIKey(
                key=key,
                user_id=user_id,
                provider=provider,
                model=model
            )
            db_session.add(api_key)
            db_session.commit()
            return {"success": True, "id": api_key.id}
        except Exception as e:
            db_session.rollback()
            return {"error": str(e)}