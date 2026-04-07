# API Reference

BetterMind CRM exposes a REST API at `/api/*`. Interactive Swagger docs are available at `/docs` when running.

## Authentication

All endpoints except `/api/login` require a Bearer token.

```
Authorization: Bearer <token>
```

Get a token via `POST /api/login`. Tokens are valid for 24 hours.

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
| category | string | Filter by category name (dynamic, see `GET /api/categories`) |
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

## Category Endpoints

### GET /api/categories

List all categories with their subcategories. Each category includes `id`, `name`, `display_name`, `icon`, `sort_order`, and a nested `subcategories` array.

### GET /api/categories/{id}

Get a single category with its subcategories. Returns 404 if not found.

### POST /api/categories

Create a new category.

```json
{
  "name": "legislator",
  "display_name": "Legislators",
  "icon": "\ud83c\udfdb\ufe0f",
  "sort_order": 4
}
```

**Required:** `name`

**Optional:** `display_name` (defaults to title-cased name), `icon` (default: clipboard), `sort_order` (default: 0)

Returns 409 if a category with that name already exists.

### PUT /api/categories/{id}

Partial update. Include only the fields you want to change (`name`, `display_name`, `icon`, `sort_order`).

### DELETE /api/categories/{id}

Delete a category. Returns 409 if any contacts still reference this category.

## Subcategory Endpoints

### GET /api/subcategories

List all subcategories. Optional `category_id` query parameter to filter by parent category.

### POST /api/subcategories

Create a new subcategory.

```json
{
  "category_id": 4,
  "name": "National",
  "display_name": "National (Federal)",
  "sort_order": 1
}
```

**Required:** `category_id`, `name`

**Optional:** `display_name` (defaults to name), `sort_order` (default: 0)

Returns 404 if the parent category does not exist. Returns 409 if the subcategory name already exists within that category.

### PUT /api/subcategories/{id}

Partial update. Include only the fields you want to change (`name`, `display_name`, `sort_order`, `category_id`).

### DELETE /api/subcategories/{id}

Delete a subcategory. Returns 409 if any contacts still reference this subcategory.

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
