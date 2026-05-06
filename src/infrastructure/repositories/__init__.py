"""Driven-adapter repository implementations.

Each module implements a domain repository Protocol against PostgreSQL via
SQLAlchemy. Maps ORM rows to pure-domain entities at the boundary so domain
code never sees SQLAlchemy.
"""
