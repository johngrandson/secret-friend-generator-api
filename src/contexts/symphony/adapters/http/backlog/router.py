"""Shared APIRouter instance for all Backlog HTTP endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/backlog", tags=["backlog"])
