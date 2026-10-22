import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parent / ".env")

client = Groq()  # lit GROQ_API_KEY

print("\n--- Modèles accessibles sur Groq ---")
for model in client.models.list().data:
    print(f"- {model.id}")
