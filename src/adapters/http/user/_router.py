"""Shared APIRouter instance for all User HTTP endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])
