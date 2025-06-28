
from fastapi import FastAPI
from pydantic import BaseModel
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

api_key = os.getenv("OPENAI_API_KEY")
app = FastAPI()

class DocIn(BaseModel):
    text: str

@app.post("/summarize")
async def summarize(doc: DocIn): 
    if not api_key:
        return {"summary": "OpenAI API key not found in environment."}
    else:
        openai = OpenAI()
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {
                    "role": "user",
                    "content": f"Explain in plain English: {doc.text[:2000]}"
                }
            ]
        )
        return {"summary": resp.choices[0].message.content}
