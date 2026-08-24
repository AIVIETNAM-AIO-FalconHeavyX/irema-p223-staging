"""Canonical retrieval roles and fail-closed document access policy."""

from __future__ import annotations

_ROLE_ALIASES = {
    "accountant": "accounting",
    "accounting": "accounting",
    "ketoan": "accounting",
    "sale": "sales",
    "sales": "sales",
    "technician": "technician",
    "ktv": "technician",
    "manager": "owner",
    "owner": "owner",
    "general": "general",
    "vinfast": "vinfast",
}

_ALLOWED_DOCUMENT_ROLES = {
    "accounting": frozenset({"accounting", "general"}),
    "sales": frozenset({"sales", "general"}),
    "technician": frozenset({"technician", "general"}),
    "owner": frozenset({"accounting", "sales", "technician", "owner", "general"}),
    "general": frozenset({"general"}),
    "vinfast": frozenset({"vinfast", "general"}),
}


def normalize_retrieval_role(role: str | None) -> str | None:
    """Return a canonical role, or ``None`` for missing/unknown values."""
    normalized = str(role or "").strip().casefold()
    return _ROLE_ALIASES.get(normalized)


def allowed_document_roles(role: str | None, access_scope: list[str] | None = None) -> frozenset[str]:
    """Return the maximum allowed document roles for an authenticated role.

    ``access_scope`` may narrow the role policy, but can never widen it.
    """
    canonical_role = normalize_retrieval_role(role)
    if canonical_role is None:
        return frozenset()

    maximum = _ALLOWED_DOCUMENT_ROLES[canonical_role]
    if not access_scope:
        return maximum

    requested = {normalized for item in access_scope if (normalized := normalize_retrieval_role(item)) is not None}
    requested.add(canonical_role)
    requested.add("general")
    return frozenset(maximum.intersection(requested))
