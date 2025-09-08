# src/llm.py
from groq import Groq
import os
from src.config import GROQ_API_KEY

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_llm(prompt: str, model: str = "llama-3.1-8b-instant"):
    """
    Call Groq's LLM with the given prompt and return response content.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are BizAnalyst AI, a professional business analyst assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content
