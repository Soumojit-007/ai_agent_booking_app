import os
import logging
import traceback

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from config.settings import settings

# ✅ Correct OpenAI exception import for modern SDK (v1.x)
from openai import OpenAIError, RateLimitError

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class LLMService:
    def __init__(self):
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key

        try:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",  # ✅ Force model version
                temperature=settings.agent_temperature
            )
            logger.info("✅ LLM initialized successfully")
        except Exception as e:
            logger.error("❌ Failed to initialize LLM: %s", str(e))
            raise

    def generate_response(self, messages: list[dict]) -> str:
        """
        Generate a response using the LLM. Expects messages as:
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Book a slot for tomorrow at 3 PM."}
        ]
        """
        try:
            formatted_messages = []
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content", "")

                if role == "system":
                    formatted_messages.append(SystemMessage(content=content))
                elif role == "user":
                    formatted_messages.append(HumanMessage(content=content))
                else:
                    logger.warning(f"⚠️ Unknown role: {role}")

            response = self.llm.invoke(formatted_messages)
            return response.content

        except RateLimitError as re:
            logger.error("❌ Rate limit exceeded: %s", str(re))
            return "⚠️ I’m currently unable to connect to the AI service due to usage limits. Please try again shortly."

        except OpenAIError as oe:
            logger.error("❌ OpenAI API error: %s", str(oe))
            return "⚠️ There was a problem communicating with the AI service. Please try again later."

        except Exception as e:
            logger.error("❌ Unexpected error during LLM response generation: %s", str(e))
            traceback.print_exc()
            return "⚠️ I encountered an internal error while trying to respond. Please try again later."


# ✅ Global instance
llm_service = LLMService()
