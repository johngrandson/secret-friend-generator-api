"""Shared APIRouter instance for all Plan HTTP endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/plans", tags=["plans"])
