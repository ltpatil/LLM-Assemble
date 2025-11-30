import os
import sys
import logging
import asyncio
from typing import List, Dict, Any, Optional


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import openai
import anthropic
import google.generativeai as genai
import google.api_core.exceptions
from groq import Groq, AsyncGroq

import config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMResponse:
    """Standardized response object for all LLM providers."""
    def __init__(self, provider_name: str, text: str, model_name: str):
        self.provider_name = provider_name
        self.text = text.strip() 
        self.model_name = model_name

    def to_dict(self):
        return {
            "provider_name": self.provider_name,
            "text": self.text,
            "model_name": self.model_name
        }

class LLMProviders:
    def __init__(self):
        
        self.openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
        self.anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY) if config.ANTHROPIC_API_KEY else None
        self.groq_client = Groq(api_key=config.GROQ_API_KEY) if config.GROQ_API_KEY else None
        
        if config.GOOGLE_API_KEY:
            genai.configure(api_key=config.GOOGLE_API_KEY)
            self.google_model = genai.GenerativeModel(config.GOOGLE_MODEL)
        else:
            self.google_model = None
        
        logger.info("LLM Providers Service Initialized.")

    def _format_prompt(self, user_prompt: str) -> str:
        """Helper to enforce concise answers via prompt engineering."""
        return (
            f"Provide a direct, concise answer to the following question. "
            f"Use plain text only, no markdown formatting.\n\n"
            f"Question: {user_prompt}"
        )

    async def query_openai(self, prompt: str, model: str = config.OPENAI_MODEL) -> Optional[LLMResponse]:
        if not self.openai_client: return None
        try:
            chat_completion = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Answer concisely in plain text without markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return LLMResponse("OpenAI", chat_completion.choices[0].message.content, model)
        except Exception as e:
            logger.error(f"OpenAI request failed: {e}")
            return None

    async def query_anthropic(self, prompt: str, model: str = config.ANTHROPIC_MODEL) -> Optional[LLMResponse]:
        if not self.anthropic_client: return None
        try:
            response = await self.anthropic_client.messages.create(
                model=model,
                max_tokens=300,
                messages=[{"role": "user", "content": self._format_prompt(prompt)}]
            )
            return LLMResponse("Anthropic", response.content[0].text, model)
        except Exception as e:
            logger.error(f"Anthropic request failed: {e}")
            return None

    async def query_google_gemini(self, prompt: str, model: str = config.GOOGLE_MODEL) -> Optional[LLMResponse]:
        if not self.google_model: return None
        
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]

        try:
            response = await self.google_model.generate_content_async(
                self._format_prompt(prompt),
                generation_config=genai.types.GenerationConfig(temperature=0.3, max_output_tokens=300),
                safety_settings=safety_settings
            )

            if not response.candidates:
                logger.warning(f"Google Gemini blocked response. Feedback: {response.prompt_feedback}")
                return None
            
            return LLMResponse("Google Gemini", response.text.strip(), model)
            
        except Exception as e:
            logger.error(f"Google Gemini request failed: {e}")
            return None

    async def query_groq(self, prompt: str, model: str, provider_label: str) -> Optional[LLMResponse]:
        """
        Queries Groq API. Accepts provider_label to distinguish Llama 3 from GPT-OSS.
        """
        if not self.groq_client: return None
        
        
        async_client = AsyncGroq(api_key=config.GROQ_API_KEY)

        try:
            chat_completion = await async_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Answer concisely in one sentence. Plain text only."},
                    {"role": "user", "content": prompt}
                ],
                model=model,
                temperature=0.3,
            )
            return LLMResponse(provider_label, chat_completion.choices[0].message.content, model)
        except Exception as e:
            logger.error(f"Groq ({model}) request failed: {e}")
            return None

    async def get_all_llm_responses(self, prompt: str) -> List[LLMResponse]:
        """Fan-out: Queries all configured providers in parallel."""
        tasks = []
        
      
        if self.google_model:
            tasks.append(self.query_google_gemini(prompt))
            
      
        if self.groq_client:
            
            model_llama = getattr(config, 'GROQ_MODEL_LLAMA', "llama-3.3-70b-versatile")
            tasks.append(self.query_groq(prompt, model=model_llama, provider_label="Groq (Llama 3)"))
            
        
        if self.groq_client:
            model_openai = getattr(config, 'GROQ_MODEL_OPENAI', "openai/gpt-oss-120b")
            tasks.append(self.query_groq(prompt, model=model_openai, provider_label="Groq (GPT-OSS)"))

        
        if self.openai_client:
            tasks.append(self.query_openai(prompt))
        if self.anthropic_client:
            tasks.append(self.query_anthropic(prompt))
        
        logger.info(f"Dispatching {len(tasks)} LLM queries...")
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        
        valid_responses = [resp for resp in responses if isinstance(resp, LLMResponse)]
        logger.info(f"Successfully received {len(valid_responses)} valid responses.")
        
        return valid_responses