from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from database import initialize
from ai_interpreter import interpret, UnsupportedQuestion
from analytics import execute

@asynccontextmanager
async def lifespan(app):
    initialize()
    yield

app = FastAPI(title='InsightAI Business Intelligence API',version='1.0.0',lifespan=lifespan)

class Question(BaseModel):
    question: str = Field(min_length=1,max_length=500)

@app.get('/health')
def health(): return {'status':'ok'}

@app.post('/ask')
def ask(request: Question):
    print(f"[API] Received question: {request.question}", flush=True)

    try:
        selection = interpret(request.question)
        print(f"[API] Interpreter result: {selection}", flush=True)

        result = execute(
            selection['intent'],
            selection.get('params')
        )

        print("[API] Analytics completed successfully.", flush=True)
        return result

    except UnsupportedQuestion as exc:
        print(f"[API] Unsupported question: {exc}", flush=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    except ValueError as exc:
        print(f"[API] Validation error: {exc}", flush=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
