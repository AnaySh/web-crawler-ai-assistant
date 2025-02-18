from typing import Optional, List, Dict
from models import APIKey, QAPair, Provider, Model
from db import db_session
from config import Config
from providers import AIProviderFactory

class AIService:
    @staticmethod
    def get_api_key(provider: str, user_id: Optional[str] = None) -> Optional[APIKey]:
        query = APIKey.query.filter_by(provider=provider, is_valid=True)
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.first()

    @staticmethod
    def ask_question(question: str, context: str, provider: str = "openai", model: Optional[str] = None, user_id: Optional[str] = None) -> Dict:
        # Validate provider
        if provider not in Config.SUPPORTED_PROVIDERS:
            return {"error": f"Unsupported provider. Must be one of: {list(Config.SUPPORTED_PROVIDERS.keys())}"}
        
        # Validate model if provided
        if model and model not in Config.SUPPORTED_PROVIDERS[provider]:
            return {"error": f"Unsupported model for {provider}. Must be one of: {Config.SUPPORTED_PROVIDERS[provider]}"}
        
        # Get API key
        api_key = AIService.get_api_key(provider, user_id)
        if not api_key:
            return {"error": f"No valid API key found for provider: {provider}"}
        
        # Create provider instance
        provider_instance = AIProviderFactory.create_provider(provider, api_key.key)
        if not provider_instance:
            return {"error": f"Failed to initialize provider: {provider}"}
        
        # Use the model from the API key if none specified
        model_to_use = model or api_key.model
        
        # Make the API call
        return provider_instance.ask_question(question, context, model_to_use)

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