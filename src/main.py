
from bot_handler import BotHandler
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Request
from contextlib import asynccontextmanager
import os
import uvicorn

load_dotenv()
TREND_API_HOST = os.getenv("TREND_API_HOST")
SBF_API_HOST = os.getenv("SBF_API_HOST")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sessions = {}
    app.state.bot_handler = BotHandler(TREND_API_HOST, SBF_API_HOST)
    yield

app = FastAPI(openapi_url="/swagger.json", lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "online"}


@app.post("/api/analysis")
async def create_request(request: Request, background_tasks: BackgroundTasks):
    request_body = await request.json()
    response, query_session = app.state.bot_handler.process_create_request(
        request_body)

    if query_session is None:
        return response

    background_tasks.add_task(
        app.state.bot_handler.track_analysis_progress,
        query_session
    )

    app.state.sessions[request_body["conversationId"]] = query_session

    return response


@app.post("/api/analysis/repeat")
async def repeat_request(request: Request, background_tasks: BackgroundTasks):
    request_body = await request.json()

    if request_body["conversationId"] not in app.state.sessions:
        return {"text": "Sorry, I can't find a previous query. Please start a new one.", "closeContext": True}

    response, query_session = app.state.bot_handler.process_repeat_request(
        request_body, app.state.sessions[request_body["conversationId"]])

    if query_session is None:
        return response

    background_tasks.add_task(
        app.state.bot_handler.track_progress,
        query_session
    )

    app.state.sessions[request_body["conversationId"]] = query_session

    return response


@app.post("/api/citrec")
async def create_citrec_request(request: Request, background_tasks: BackgroundTasks):
    request_body = await request.json()
    print(request_body)
    response, query_session = app.state.bot_handler.process_citation_recommendation(
        request_body
    )

    if query_session is None:
        return response

    background_tasks.add_task(
        app.state.bot_handler.track_citrec_progress,
        query_session
    )

    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5999)
