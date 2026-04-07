"""
BetterMind CRM - Pydantic Models
Request/response models for all API endpoints.
"""
from typing import Optional
from pydantic import BaseModel, field_validator


def _validate_email(v: str) -> str:
    """Shared email validation: must contain @ and a dot in the domain."""
    if "@" not in v or "." not in v.split("@")[-1]:
        raise ValueError("Invalid email format")
    return v.strip().lower()


VALID_STATUSES = frozenset({
    "active", "diligence", "outreach", "follow_up", "scheduled", "passed",
    "connected", "recruiting", "searching", "contact", "cold", "complete",
    "applied", "planning", "identified", "meeting", "term_sheet", "closed", "dead",
})


# ==================== AUTH ====================

class LoginRequest(BaseModel):
    """Login credentials."""
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v):
        return _validate_email(v)


class UserCreate(BaseModel):
    """New user registration (admin only)."""
    email: str
    password: str
    name: Optional[str] = None
    role: str = "user"

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v):
        return _validate_email(v)

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, v):
        if v not in ("admin", "user"):
            raise ValueError("Role must be 'admin' or 'user'")
        return v


class PasswordUpdate(BaseModel):
    """Password change request."""
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


# ==================== CONTACTS ====================

class ContactCreate(BaseModel):
    """Create a new contact. Requires first_name, category, and status."""
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    email_secondary: Optional[str] = None
    phone: Optional[str] = None
    phone_secondary: Optional[str] = None
    linkedin_url: Optional[str] = None
    organization_id: Optional[int] = None
    title: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    status: str
    tier: Optional[int] = None
    last_contact_date: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[str] = None
    notes: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = "US"
    website: Optional[str] = None
    twitter_url: Optional[str] = None

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v):
        if v not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}")
        return v


class ContactUpdate(BaseModel):
    """Partial update for an existing contact. Include only fields to change."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    email_secondary: Optional[str] = None
    phone: Optional[str] = None
    phone_secondary: Optional[str] = None
    linkedin_url: Optional[str] = None
    organization_id: Optional[int] = None
    title: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    status: Optional[str] = None
    tier: Optional[int] = None
    last_contact_date: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[str] = None
    notes: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    twitter_url: Optional[str] = None

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v):
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}")
        return v


class BulkContactUpdate(BaseModel):
    """Bulk update multiple contacts at once."""
    contact_ids: list[int]
    status: Optional[str] = None
    category: Optional[str] = None
    tier: Optional[int] = None

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v):
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}")
        return v


# ==================== ORGANIZATIONS ====================

class OrganizationCreate(BaseModel):
    """Create a new organization."""
    name: str
    type: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    focus_areas: Optional[str] = None
    notes: Optional[str] = None


class OrganizationUpdate(BaseModel):
    """Partial update for an existing organization."""
    name: Optional[str] = None
    type: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    focus_areas: Optional[str] = None
    notes: Optional[str] = None


# ==================== INTERACTIONS ====================

class InteractionCreate(BaseModel):
    """Log a new interaction (email, call, meeting, note)."""
    contact_id: int
    type: str
    channel: Optional[str] = None
    subject: Optional[str] = None
    summary: Optional[str] = None
    date: str


class InteractionUpdate(BaseModel):
    """Partial update for an existing interaction."""
    type: Optional[str] = None
    channel: Optional[str] = None
    subject: Optional[str] = None
    summary: Optional[str] = None
    date: Optional[str] = None


# ==================== DEALS ====================

class DealCreate(BaseModel):
    """Create a new deal in the pipeline."""
    contact_id: Optional[int] = None
    organization_id: Optional[int] = None
    deal_name: str
    stage: str
    amount: Optional[str] = None
    probability: Optional[int] = None
    notes: Optional[str] = None


class DealUpdate(BaseModel):
    """Partial update for an existing deal."""
    contact_id: Optional[int] = None
    organization_id: Optional[int] = None
    deal_name: Optional[str] = None
    stage: Optional[str] = None
    amount: Optional[str] = None
    probability: Optional[int] = None
    notes: Optional[str] = None


# ==================== PROGRAMS ====================

class ProgramCreate(BaseModel):
    """Create a new program."""
    name: str
    organization_id: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    value: Optional[str] = None
    primary_contact_id: Optional[int] = None
    notes: Optional[str] = None


class ProgramUpdate(BaseModel):
    """Partial update for an existing program."""
    name: Optional[str] = None
    organization_id: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    value: Optional[str] = None
    primary_contact_id: Optional[int] = None
    notes: Optional[str] = None


# ==================== TAGS ====================

class TagCreate(BaseModel):
    """Create a new tag."""
    name: str

    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v):
        v = v.strip().lower().replace(" ", "-")
        if not v:
            raise ValueError("Tag name cannot be empty")
        return v
