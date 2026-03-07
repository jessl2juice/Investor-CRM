# API Reference

BetterMind CRM exposes a REST API at `/api/*`. Interactive Swagger docs are available at `/docs` when running.

## Authentication

All endpoints except `/api/login` and `/api/help` require a Bearer token.

```
Authorization: Bearer <token>
```

Get a token via `POST /api/login`. Tokens are valid for 7 days.

## Auth Endpoints

### POST /api/login

Authenticate and receive a token.

**Request:**

```json
{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

**Response:**

```json
{
  "token": "...",
  "email": "user@example.com",
  "name": "User Name",
  "role": "admin"
}
```

### GET /api/me

Returns the current user's email and role from the token.

## Contact Endpoints

### GET /api/contacts

List contacts with optional filters.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| category | string | Filter by category (investor, google, team, etc.) |
| status | string | Filter by status (active, outreach, passed, etc.) |
| tier | int | Filter by tier number |
| search | string | Full-text search across name, email, title, notes, org |
| limit | int | Max results (default 200, max 500) |
| offset | int | Pagination offset |

### GET /api/contacts/{id}

Get a single contact with their interactions and deals.

### POST /api/contacts

Create a new contact.

**Required fields:** `first_name`, `category`, `status`

**Optional fields:** `last_name`, `email`, `email_secondary`, `phone`, `phone_secondary`, `linkedin_url`, `organization_id`, `title`, `subcategory`, `tier`, `last_contact_date`, `next_action`, `next_action_date`, `notes`, `address_line1`, `address_line2`, `city`, `state`, `zip`, `country`, `website`, `twitter_url`

### PUT /api/contacts/{id}

Partial update. Include only the fields you want to change.

### DELETE /api/contacts/{id}

Delete a contact.

## Organization Endpoints

### GET /api/organizations

List all organizations.

### POST /api/organizations

Create an organization. **Required:** `name`

### GET /api/organizations/{id}

Get an organization with its associated contacts.

### PUT /api/organizations/{id}

Partial update.

### DELETE /api/organizations/{id}

Delete an organization. Unlinks associated contacts.

## Interaction Endpoints

### GET /api/interactions

List interactions. Optional `contact_id` filter and `limit` (default 50).

### POST /api/interactions

Log a new interaction. Automatically updates the contact's `last_contact_date`.

**Required:** `contact_id`, `type`, `date`

**Optional:** `channel`, `subject`, `summary`

### GET /api/interactions/{id}

Get a single interaction.

### PUT /api/interactions/{id}

Partial update.

### DELETE /api/interactions/{id}

Delete an interaction.

## Deal Endpoints

### GET /api/deals

List deals. Optional `stage` and `contact_id` filters.

### POST /api/deals

Create a deal. **Required:** `deal_name`, `stage`

**Optional:** `contact_id`, `organization_id`, `amount`, `probability`, `notes`

### GET /api/deals/{id}

Get a deal with contact and organization info.

### PUT /api/deals/{id}

Partial update.

### DELETE /api/deals/{id}

Delete a deal.

## Program Endpoints

### GET /api/programs

List programs. Optional `status` filter.

### POST /api/programs

Create a program. **Required:** `name`

### GET /api/programs/{id}

Get a program with org and contact info.

### PUT /api/programs/{id}

Partial update.

### DELETE /api/programs/{id}

Delete a program.

## Tag Endpoints

### GET /api/tags

List all tags.

### POST /api/tags

Create a tag. **Required:** `name`

### DELETE /api/tags/{id}

Delete a tag and remove it from all contacts.

### GET /api/contacts/{id}/tags

Get all tags for a contact.

### POST /api/contacts/{contact_id}/tags/{tag_id}

Assign a tag to a contact.

### DELETE /api/contacts/{contact_id}/tags/{tag_id}

Remove a tag from a contact.

## Bulk Operations

### PUT /api/bulk/contacts

Bulk update status, category, or tier for multiple contacts.

```json
{
  "contact_ids": [1, 2, 3],
  "status": "active",
  "tier": 1
}
```

## Other Endpoints

### GET /api/stats

Dashboard statistics (total contacts, by category, by status, active investors, deals, interactions, organizations).

### GET /api/help

Returns the user manual content as `{"content": "..."}`.

## User Management (Admin Only)

### GET /api/users

List all users. Requires admin role.

### POST /api/users

Create a user. Requires admin role.

```json
{
  "email": "new@example.com",
  "password": "securepassword",
  "name": "New User",
  "role": "user"
}
```

### PUT /api/users/{id}/password

Change a user's password. Users can change their own; admins can change any.

### DELETE /api/users/{id}

Delete a user. Requires admin role. Cannot delete yourself.
