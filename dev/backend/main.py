
from fastapi import FastAPI
from pydantic import BaseModel
import os
import openai
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

openai.api_key = os.getenv("OPENAI_API_KEY")
app = FastAPI()

class DocIn(BaseModel):
    text: str

@app.post("/summarize")
async def summarize(doc: DocIn):
    if not openai.api_key:
        return {"summary": "OpenAI API key not found in environment."}

    resp = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0.2,
        messages=[
            {
                "role": "user",
                "content": f"Explain in plain English:

{doc.text[:2000]}"
            }
        ]
    )
    return {"summary": resp.choices[0].message.content}
