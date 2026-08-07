import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.models import QueryRequest, QueryResponse
from api.services.query_service import run_question


app = FastAPI(
    title="Beavelo API",
    description="Natural-language business questions to safe SQL results.",
    version="0.1.0",
)

allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8501",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=["X-Process-Time"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start_time:.3f}"
    return response


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "beavelo-api"}


@app.post("/v1/query", response_model=QueryResponse)
def query_data(request: QueryRequest):
    return run_question(request.question)