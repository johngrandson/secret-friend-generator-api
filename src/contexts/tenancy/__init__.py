"""Tenancy bounded context.

Hosts organization, membership, and role concerns. Organization is the aggregate
root binding users (by id) to their tenant scope. Symphony resources are not
tenant-scoped at this stage (deferred until a concrete requirement appears).
"""
