from fastapi import FastAPI
from pydantic import BaseModel

from idea_generator import run_idea_generator

ige_app = FastAPI()


class IgeRequest(BaseModel):
    context: str


@ige_app.get("/")
def read_path():
    return {"message": "IGE prototype API"}


@ige_app.post("/generate")
def generate(request: IgeRequest):
    result = run_idea_generator(request.context)
    return result