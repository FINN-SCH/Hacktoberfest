from fastapi import Request
from sqlmodel import Session

def get_db(request: Request):
    with Session(request.app.state.engine) as db:
        yield db

def get_settings(request: Request):
    return request.app.state.settings

def get_providers(request: Request):
    return request.app.state.providers
