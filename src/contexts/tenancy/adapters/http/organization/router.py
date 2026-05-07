"""Shared APIRouter instance for all Organization HTTP endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/organizations", tags=["organizations"])
