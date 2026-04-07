# BetterMind CRM - User Manual

**Version:** 1.2 · **Last updated:** April 7, 2026
**Live URL:** [https://bettermind.buzz](https://bettermind.buzz)

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Dashboard Overview](#2-dashboard-overview)
3. [Managing Contacts](#3-managing-contacts)
4. [Investor Pipeline](#4-investor-pipeline)
5. [Programs & Milestones](#5-programs--milestones)
6. [Logging Interactions](#6-logging-interactions)
7. [User Management (Admin)](#7-user-management-admin)
8. [Using the API Directly](#8-using-the-api-directly)
9. [Tips & Workflows](#9-tips--workflows)
10. [Troubleshooting](#10-troubleshooting)

**[Appendix A: API Reference](#appendix-a-api-reference)**

---

## 1. Getting Started

### Signing In

1. Navigate to [https://bettermind.buzz](https://bettermind.buzz)
2. Enter your **email** and **password**
3. Click **Sign In**

Your session lasts 24 hours. After that you'll be prompted to sign in again.

### First-Time Setup

If you're a new user, an admin needs to create your account first (see [Section 7](#7-user-management-admin)). There is no self-registration.

### Signing Out

Click **Sign Out** in the top-right corner of the header bar.

---

## 2. Dashboard Overview

After signing in, you'll see the main CRM interface with these elements:

### Header Bar

The dark header at the top shows:

- **BetterMind CRM** branding with the tagline "Fundraising · Legislators · Google · Team · Pipeline"
- **Quick stats**  - four key numbers at a glance:
  - **Contacts**  - total people in the CRM
  - **Active**  - investors with active status
  - **Deals**  - number of deals in the pipeline
  - **Logs**  - total interaction records
- **Sign Out** button

### Navigation Tabs

Below the header, tabs let you switch between views:

| Tab | Icon | What it shows |
|-----|------|---------------|
| **All** | 📋 | Every contact across all categories |
| **Investors** | 💰 | Only contacts categorized as `investor` |
| **Legislators** | 🏛️ | Only contacts categorized as `legislator` |
| **Google** | 🔷 | Only contacts categorized as `google` |
| **Team** | 👤 | Only contacts categorized as `team` |
| **Advisors** | 🧠 | Only contacts categorized as `advisor` |
| **Pipeline** | 📊 | Fundraising deals view (not contacts) |
| **Programs** | 🚀 | Programs & milestones view |
| **Settings** | ⚙️ | User management (admin only) |

Navigation tabs are dynamically loaded from the categories API. If new categories are added, they will appear as tabs automatically.

The **Settings** tab only appears if you have the **admin** role.

---

## 3. Managing Contacts

### Browsing Contacts

On any contact tab (All, Investors, Legislators, Google, Team, Advisors), you see a list of contacts. Each row shows:

- **Category icon** (💰 investor, 🏛️ legislator, 🔷 Google, 👤 team, 🧠 advisor, 🤝 partner, 🔧 vendor, 🎓 university, 📰 media, 📋 other)
- **Name** and **tier badge** (T1, T2, T3, T4) if assigned
- **Title** and **organization**
- **Contact completeness dot:**
  - 🟢 Green = has both email and phone
  - 🟡 Yellow = has email or phone (but not both)
  - 🔴 Red = missing both email and phone
- **Clickable contact icons:**
  - ✉️ Email  - click to open a new email (mailto: link)
  - 📞 Phone  - click to dial (tel: link)
  - 🔗 LinkedIn  - click to open profile in a new tab
  - Clicking these icons does **not** open the contact detail panel
- **Status badge** (color-coded: green = active, blue = outreach, purple = follow_up, etc.)
- **Last contact date**

### Searching

Use the **search bar** at the top of the contact list. It searches across:
- First name, last name
- Email
- Title
- Notes
- Subcategory
- Organization name

Just start typing  - results filter in real time.

### Filtering by Status

Below the search bar, **status pills** let you filter contacts by their current status:
- Click a status pill (e.g., "active", "outreach", "follow up") to show only those contacts
- Click **All** to clear the filter
- Available statuses depend on what's in your data

### Viewing a Contact

Click any contact row to open the **Contact Detail** panel. The panel is organized into these sections:

**Header:**
- **Name**, **title**, and **organization**
- **Status badge**, **tier**, and **category label**
- **Edit** button  - enters edit mode for contact information (see below)
- **Delete** button  - permanently removes the contact after confirmation
- **✕** button  - closes the panel

**Contact Information Card** (displayed prominently at the top):
- **Email** and **Email (Secondary)**  - clickable mailto: link + Copy button
- **Phone** and **Phone (Secondary)**  - clickable tel: link + Copy button
- **LinkedIn**  - clickable link that opens in a new tab
- **Website**  - clickable link that opens in a new tab
- **Twitter/X**  - clickable link that opens in a new tab
- **Address**  - clickable link that opens Google Maps
- Empty fields are hidden automatically. If no contact info exists at all, a helpful message is shown
- The **Copy** button changes to "✓ Copied" for 1.5 seconds after clicking

**Pipeline & Actions:**
- **Last contact date**
- **Next action**  - highlighted in blue if set, with optional date

**Notes**  - free-text notes field

**Deals**  - any deals associated with this contact, with deal name, amount, stage badge, and probability

**Activity Log**  - chronological list of all interactions (emails, calls, meetings, notes) with date, type, subject, and summary

### Editing Contact Information

Click the **Edit** button in the contact detail header to enter edit mode on the Contact Information Card:

1. **Category** and **Subcategory** dropdowns appear at the top, populated dynamically from the database. Changing the category resets the subcategory. Subcategories are filtered to show only those belonging to the selected category
2. All contact fields become editable input fields (email, phone, LinkedIn, website, Twitter/X)
3. Address expands into individual fields: Address Line 1, Address Line 2, City, State, Zip, Country
4. Click **Save** to persist changes, or **Cancel** to discard
5. Edit mode only affects the Contact Information Card  - other fields (name, status, notes, etc.) are not editable here

### Deleting a Contact

1. Open the contact detail panel
2. Click the red **Delete** button in the header
3. Confirm in the popup dialog
4. The contact is permanently removed and the list refreshes

### Logging a Quick Note

At the bottom of the Contact Detail panel:

1. Type your note in the **"Add a note or log activity..."** field
2. Press **Enter** or click **Log**
3. The note is saved as an interaction and the contact's last contact date is updated automatically

### Closing the Detail Panel

Click the **✕** button in the top-right of the panel, or click the dark overlay behind it. The contact list automatically refreshes when you close the panel after edits.

---

## 4. Investor Pipeline

Click the **Pipeline** tab (📊) to see the fundraising deal tracker.

Each deal card shows:
- **Deal name** (e.g., "Seed Round  - Sequoia")
- **Contact name** and **organization**
- **Amount** (e.g., "$500K")
- **Stage badge**  - color-coded by stage:
  - `identified` → gray
  - `outreach` → blue
  - `meeting` → teal
  - `diligence` → yellow
  - `term_sheet` → green
  - `closed` → bright green
  - `passed` → gray
  - `dead` → dark gray
- **Probability ring**  - visual indicator showing deal likelihood (0–100%)

Deals are sorted by probability (highest first).

**Click a deal card** to open the associated contact's detail panel (if the deal has a linked contact).

### Managing Deals via API

The web UI currently shows deals in read-only mode. To **create, update, or delete deals**, use the API directly (see [Appendix A](#deals-pipeline-1)).

---

## 5. Programs & Milestones

Click the **Programs** tab (🚀) to see all programs and milestones.

Each program card shows:
- **Program name** (e.g., "Google for Startups Cloud Program")
- **Value** (e.g., "$200K"), **start date**, and **primary contact**
- **Notes**  - additional context
- **Status badge**  - `active`, `applied`, `accepted`, `complete`, or `planning`

### Managing Programs via API

Like deals, the web UI shows programs in read-only mode. To **create, update, or delete programs**, use the API (see [Appendix A](#programs-1)).

---

## 6. Logging Interactions

Interactions are the activity log  - every email, call, meeting, LinkedIn message, or note.

### From the Contact Detail Panel

The quickest way: open a contact and use the note field at the bottom (see [Section 3](#logging-a-quick-note)). This creates a `note` type interaction.

### Via the API

For richer interaction logging (specifying type, channel, subject), use the API:

```
POST /api/interactions
{
  "contact_id": 5,
  "type": "email_sent",
  "channel": "email",
  "subject": "Follow-up on demo",
  "summary": "Sent deck and availability for next week",
  "date": "2026-03-05"
}
```

**Supported types:** `email_sent`, `email_received`, `email`, `linkedin_dm`, `linkedin_connect`, `meeting`, `meeting_scheduled`, `call`, `intro`, `follow_up`, `pitch`, `note`, `demo`, `webinar`, `event`, `referral`, `other`

**Supported channels:** `email`, `linkedin`, `phone`, `zoom`, `google_meet`, `in_person`, `slack`, `calendly`, `twitter`, `text`, `teams`, `other`

---

## 7. User Management (Admin)

Only users with the **admin** role can access the Settings tab.

### Viewing Users

Click the **Settings** tab (⚙️). You'll see a list of all user accounts with:
- **Name** and **email**
- **Role badge** (purple = admin, blue = user)
- **Password** and **Delete** buttons

### Adding a New User

1. Click **+ Add User**
2. Fill in **Email**, **Name**, **Password**, and select a **Role** (User or Admin)
3. Click **Create User**

### Changing a Password

1. Click **Password** next to the user
2. Enter the new password in the field that appears
3. Click **Update**

Any user can change their own password. Admins can change any user's password.

### Deleting a User

1. Click **Delete** next to the user
2. Confirm in the popup dialog

You cannot delete your own account while logged in.

---

## 8. Using the API Directly

BetterMind CRM has a full REST API that can be used by external tools (Claude, scripts, integrations). The web UI only exposes a subset of what the API can do.

### Things you can ONLY do via the API

- **Create, update, or delete organizations**
- **Update or delete interactions** (web UI can only create notes)
- **Create, update, or delete deals** (web UI is read-only)
- **Create, update, or delete programs** (web UI is read-only)
- **Manage tags** (create tags, assign/remove tags on contacts)
- **Manage categories and subcategories** (create, update, delete via `/api/categories` and `/api/subcategories`)
- **Bulk update contacts** (change status/category/tier for many contacts at once)
- **Filter deals by stage** or **programs by status**

### Quick Start: Getting a Token

Every API call (except login) needs an auth token. Get one like this:

```bash
curl -X POST https://bettermind.buzz/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "yourpassword"}'
```

The response includes a `token` field. Use it in subsequent requests:

```bash
curl https://bettermind.buzz/api/contacts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Interactive API Docs

FastAPI auto-generates interactive docs at:
- **Swagger UI:** [https://bettermind.buzz/docs](https://bettermind.buzz/docs)
- **ReDoc:** [https://bettermind.buzz/redoc](https://bettermind.buzz/redoc)

See [Appendix A](#appendix-a-api-reference) for the full endpoint reference.

---

## 9. Tips & Workflows

### Daily Check-In

1. Open the CRM and check the **header stats** for a pulse
2. Click **Pipeline** to review deal progress
3. Filter contacts by **"follow_up"** status to see who needs attention
4. Click into each contact, review their activity log, and log any new interactions

### Investor Outreach Workflow

1. Add new investor contacts via the API or future UI additions
2. Set their status to `outreach`
3. Log each interaction (emails, meetings)  - the `last_contact_date` updates automatically
4. Move status through `outreach` → `meeting` → `diligence` → `follow_up` as the relationship progresses
5. Create a deal in the Pipeline when there's a concrete funding opportunity

### Bulk Status Updates

Need to mark 10 contacts as "cold" after a batch review? Use the bulk endpoint:

```bash
curl -X PUT https://bettermind.buzz/api/bulk/contacts \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"contact_ids": [1, 5, 12, 15, 18, 22, 25, 30, 33, 41], "status": "cold"}'
```

### Tagging Contacts

Tags help you group contacts across categories. For example, tag all contacts you met at a specific event:

```bash
# Create a tag
curl -X POST https://bettermind.buzz/api/tags \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "TechCrunch Disrupt 2026"}'

# Assign it to contacts
curl -X POST https://bettermind.buzz/api/contacts/5/tags/14 \
  -H "Authorization: Bearer TOKEN"
```

---

## 10. Troubleshooting

### "Invalid email or password"

- Double-check your email and password
- Passwords are case-sensitive
- If you've forgotten your password, ask an admin to reset it via the Settings tab

### Session expired / redirected to login

- Sessions last 24 hours. After that, you'll need to sign in again
- If the app was redeployed without a stable `TOKEN_SECRET`, all sessions are invalidated

### Page is blank or not loading

- Check your internet connection
- Try a hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
- Clear your browser cache and try again

### API returns 401 Unauthorized

- Your token has expired (24-hour TTL). Get a new one via `/api/login`
- Make sure the `Authorization: Bearer <token>` header is included

### API returns 422 Invalid data

- A field value violated a database constraint (e.g., invalid interaction type or deal stage)
- Check the error message for details on which field is invalid
- See [Appendix A](#appendix-a-api-reference) for valid enum values

### Contact detail won't open

- The contact may have been deleted. Refresh the page to update the list

---

# Appendix A: API Reference

Base URL: `https://bettermind.buzz/api`

All endpoints (except `/api/login`) require a Bearer token in the `Authorization` header.

---

## Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/login` | None | Login, returns token |
| GET | `/api/me` | User | Current user info |

**Login request:**

```json
{ "email": "user@example.com", "password": "secret" }
```

**Login response:**

```json
{ "token": "...", "email": "user@example.com", "name": "User", "role": "admin" }
```

---

## Contacts

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/contacts` | User | List contacts (filterable) |
| GET | `/api/contacts/{id}` | User | Single contact + interactions + deals |
| POST | `/api/contacts` | User | Create contact |
| PUT | `/api/contacts/{id}` | User | Update contact (partial) |
| DELETE | `/api/contacts/{id}` | User | Delete contact |

**Query parameters for `GET /api/contacts`:**

| Param | Description |
|-------|-------------|
| `category` | Dynamic. Use `GET /api/categories` for current list. Default categories: `investor`, `legislator`, `google`, `team`, `advisor`, `partner`, `vendor`, `university`, `media`, `other` |
| `status` | `active`, `diligence`, `outreach`, `follow_up`, `scheduled`, `passed`, `connected`, `recruiting`, `searching`, `contact`, `cold` |
| `tier` | `1`, `2`, `3`, `4` |
| `search` | Full-text search across name, email, title, notes, org name |
| `limit` | Max results (default 200, max 500) |
| `offset` | Pagination offset |

**Create contact request:**

```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@example.com",
  "email_secondary": "jane.personal@email.com",
  "phone": "555-0100",
  "phone_secondary": "555-0101",
  "linkedin_url": "https://linkedin.com/in/janesmith",
  "organization_id": 3,
  "title": "Managing Partner",
  "category": "investor",
  "subcategory": "Series A",
  "status": "outreach",
  "tier": 1,
  "next_action": "Send intro deck",
  "next_action_date": "2026-03-10",
  "notes": "Met at TechCrunch Disrupt",
  "address_line1": "2800 Sand Hill Road",
  "address_line2": "Suite 101",
  "city": "Menlo Park",
  "state": "CA",
  "zip": "94025",
  "country": "US",
  "website": "https://sequoiacap.com",
  "twitter_url": "https://twitter.com/sequoia"
}
```

**Update contact request (partial  - include only fields to change):**

```json
{
  "status": "meeting",
  "next_action": "Schedule follow-up call",
  "next_action_date": "2026-03-15",
  "website": "https://example.com",
  "city": "San Francisco",
  "state": "CA"
}
```

Set a field to `null` to clear it:

```json
{ "next_action": null, "next_action_date": null }
```

---

## Organizations

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/organizations` | User | List all organizations |
| GET | `/api/organizations/{id}` | User | Single org + its contacts |
| POST | `/api/organizations` | User | Create organization |
| PUT | `/api/organizations/{id}` | User | Update organization (partial) |
| DELETE | `/api/organizations/{id}` | User | Delete org (nulls contact refs) |

**Valid `type` values:** `vc_firm`, `cvc`, `accelerator`, `tech_company`, `university`, `hospital_system`, `consulting`, `startup`, `media`, `government`, `other`

**Create organization request:**

```json
{
  "name": "Sequoia Capital",
  "type": "vc_firm",
  "website": "https://sequoiacap.com",
  "phone": "650-854-3927",
  "city": "Menlo Park",
  "state": "CA",
  "focus_areas": "AI, Healthcare, Enterprise",
  "notes": "Tier 1 target"
}
```

---

## Interactions

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/interactions` | User | List interactions |
| GET | `/api/interactions/{id}` | User | Single interaction |
| POST | `/api/interactions` | User | Log new interaction |
| PUT | `/api/interactions/{id}` | User | Update interaction (partial) |
| DELETE | `/api/interactions/{id}` | User | Delete interaction |

**Query parameters for `GET /api/interactions`:**

| Param | Description |
|-------|-------------|
| `contact_id` | Filter by contact |
| `limit` | Max results (default 50) |

**Valid `type` values:** `email_sent`, `email_received`, `email`, `linkedin_dm`, `linkedin_connect`, `meeting`, `meeting_scheduled`, `call`, `intro`, `follow_up`, `pitch`, `note`, `demo`, `webinar`, `event`, `referral`, `other`

**Valid `channel` values:** `email`, `linkedin`, `phone`, `zoom`, `google_meet`, `in_person`, `slack`, `calendly`, `twitter`, `text`, `teams`, `other`

**Create interaction request:**

```json
{
  "contact_id": 5,
  "type": "meeting",
  "channel": "zoom",
  "subject": "Intro call with partner",
  "summary": "Discussed BetterMind thesis, they want to see traction metrics. Follow up in 2 weeks.",
  "date": "2026-03-05"
}
```

Creating an interaction automatically updates the contact's `last_contact_date`.

---

## Deals (Pipeline)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/deals` | User | List deals (filterable) |
| GET | `/api/deals/{id}` | User | Single deal with names |
| POST | `/api/deals` | User | Create deal |
| PUT | `/api/deals/{id}` | User | Update deal (partial) |
| DELETE | `/api/deals/{id}` | User | Delete deal |

**Query parameters for `GET /api/deals`:**

| Param | Description |
|-------|-------------|
| `stage` | Filter by stage |
| `contact_id` | Filter by contact |

**Valid `stage` values:** `identified`, `outreach`, `meeting`, `diligence`, `term_sheet`, `closed`, `passed`, `dead`

**Create deal request:**

```json
{
  "contact_id": 5,
  "organization_id": 3,
  "deal_name": "Seed Round  - Sequoia",
  "stage": "meeting",
  "amount": "$500K",
  "probability": 40,
  "notes": "Partner interested, need to send data room"
}
```

**Update deal stage:**

```json
{ "stage": "diligence", "probability": 60 }
```

---

## Programs

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/programs` | User | List programs (filterable) |
| GET | `/api/programs/{id}` | User | Single program with names |
| POST | `/api/programs` | User | Create program |
| PUT | `/api/programs/{id}` | User | Update program (partial) |
| DELETE | `/api/programs/{id}` | User | Delete program |

**Query parameters for `GET /api/programs`:**

| Param | Description |
|-------|-------------|
| `status` | Filter by status |

**Valid `status` values:** `active`, `applied`, `accepted`, `complete`, `planning`

**Create program request:**

```json
{
  "name": "Google for Startups Cloud Program",
  "organization_id": 10,
  "status": "active",
  "start_date": "2026-01-15",
  "end_date": "2027-01-15",
  "value": "$200K credits",
  "primary_contact_id": 8,
  "notes": "2-year cloud credits program"
}
```

---

## Tags

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/tags` | User | List all tags |
| POST | `/api/tags` | User | Create tag (409 if duplicate) |
| DELETE | `/api/tags/{id}` | User | Delete tag + remove from all contacts |
| GET | `/api/contacts/{id}/tags` | User | List tags for a contact |
| POST | `/api/contacts/{id}/tags/{tag_id}` | User | Assign tag to contact |
| DELETE | `/api/contacts/{id}/tags/{tag_id}` | User | Remove tag from contact |

**Create tag:**

```json
{ "name": "YC W26 batch" }
```

**Assign tag to contact:** `POST /api/contacts/5/tags/14` (no body needed)

**Remove tag from contact:** `DELETE /api/contacts/5/tags/14`

---

## Bulk Operations

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| PUT | `/api/bulk/contacts` | User | Update multiple contacts at once |

**Request:**

```json
{
  "contact_ids": [1, 5, 12, 15],
  "status": "cold",
  "category": "investor",
  "tier": 3
}
```

All fields except `contact_ids` are optional. Include only the ones you want to change.

**Response:**

```json
{ "updated": 4, "contact_ids": [1, 5, 12, 15] }
```

---

## Stats

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/stats` | User | Dashboard statistics |

**Response:**

```json
{
  "total_contacts": 47,
  "by_category": { "investor": 23, "google": 9, "team": 8, ... },
  "by_status": { "active": 11, "outreach": 10, "follow_up": 5, ... },
  "active_investors": 21,
  "pipeline_probability": 70,
  "active_deals": 4,
  "total_interactions": 8,
  "total_organizations": 21
}
```

---

## User Management (Admin Only)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/users` | Admin | List all users |
| POST | `/api/users` | Admin | Create user |
| PUT | `/api/users/{id}/password` | User* | Change password |
| DELETE | `/api/users/{id}` | Admin | Delete user (can't delete self) |

*Any user can change their own password. Admins can change any user's password.

**Create user:**

```json
{ "email": "newuser@company.com", "password": "securepassword", "name": "New User", "role": "user" }
```

**Change password:**

```json
{ "password": "newsecurepassword" }
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created (POST endpoints) |
| 400 | Bad request (missing or invalid input) |
| 401 | Unauthorized (missing or expired token) |
| 403 | Forbidden (insufficient role  - e.g., user trying admin endpoint) |
| 404 | Not found (resource doesn't exist) |
| 409 | Conflict (e.g., duplicate tag name) |
| 422 | Validation error (constraint violation, invalid enum value) |
| 500 | Server error |
