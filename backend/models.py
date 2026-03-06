"""
BetterMind CRM - Pydantic Models
Request/response models for all API endpoints.
"""
from typing import Optional
from pydantic import BaseModel


# ==================== AUTH ====================

class LoginRequest(BaseModel):
    """Login credentials."""
    email: str
    password: str


class UserCreate(BaseModel):
    """New user registration (admin only)."""
    email: str
    password: str
    name: Optional[str] = None
    role: str = "user"


class PasswordUpdate(BaseModel):
    """Password change request."""
    password: str


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


class BulkContactUpdate(BaseModel):
    """Bulk update multiple contacts at once."""
    contact_ids: list[int]
    status: Optional[str] = None
    category: Optional[str] = None
    tier: Optional[int] = None


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
