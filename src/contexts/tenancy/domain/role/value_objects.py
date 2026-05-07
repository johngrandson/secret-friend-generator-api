"""Role value object — RBAC roles for organization members.

A simple enum at this stage. Will be promoted to an aggregate when (and only
when) custom dynamic roles are required.
"""

from enum import Enum


class Role(str, Enum):
    """Membership roles within an organization (RBAC, fixed set)."""

    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"

    def can_manage_members(self) -> bool:
        """Owners and admins may add/remove/change members."""
        return self in (Role.OWNER, Role.ADMIN)

    def can_change_role_to(self, target: "Role") -> bool:
        """Only owners may grant/revoke OWNER role; admins manage non-owners."""
        if target is Role.OWNER:
            return self is Role.OWNER
        return self.can_manage_members()
