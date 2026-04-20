"""Assembles all agents sub-routers into a single APIRouter."""

from fastapi import APIRouter

from src.api.agents.health_route import router as health_router
from src.api.agents.invoke_route import router as invoke_router
from src.api.agents.resume_route import router as resume_router
from src.api.agents.stream_route import router as stream_router
from src.api.agents.threads_route import router as threads_router

agents_router = APIRouter(tags=["agents"])
agents_router.include_router(health_router)
agents_router.include_router(invoke_router)
agents_router.include_router(stream_router)
agents_router.include_router(resume_router)
agents_router.include_router(threads_router)
