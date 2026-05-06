"""Shared APIRouter instance for all Spec HTTP endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/specs", tags=["specs"])
