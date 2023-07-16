from fastapi import FastAPI, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from uuid import UUID
from app.website import generate_website, iterate_on_website


limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/ping")
async def ping(request: Request):
    return Response(content="pong", status_code=200)


@app.get("/start_website/")
@limiter.limit("10/minute")
async def get_story(
    request: Request,
    website_id: str,
    background_tasks: BackgroundTasks,
):
    website = generate_website(website_id)
    print("so far so good?")
    background_tasks.add_task(iterate_on_website, website_id)

    response = {"website": website}

    return JSONResponse(response)
