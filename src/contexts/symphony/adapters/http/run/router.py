"""Shared APIRouter instance for all Run HTTP endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/runs", tags=["runs"])
