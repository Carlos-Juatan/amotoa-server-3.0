# Research: Main Dashboard & Account Switcher

This document details research, decisions, and patterns selected to implement the main dashboard, profile switcher, and dynamic data isolation features.

---

## Decision 1: Database Collections & Configuration Schema

### Decision
We will establish a dedicated `accounts_config` collection in MongoDB to store the UI configuration, and use dynamic fields on generic content collections to support data isolation.

**`accounts_config` Collection**:
Stores two documents, one for each account (`car-j-works` and `car-j-home`).
```json
{
  "_id": "car-j-works",
  "visibility_settings": {
    "series": true,
    "animes": true,
    "youtube": true,
    "light_novels": true,
    "manga": true,
    "jogos": true,
    "financas": true,
    "saude_fitness": true,
    "links": true,
    "trabalho": true,
    "estudos": true,
    "filmes": true
  },
  "data_separation_settings": {
    "series": false,
    "animes": false,
    "youtube": false,
    "light_novels": false,
    "manga": false,
    "jogos": false,
    "financas": false,
    "saude_fitness": false,
    "links": false,
    "trabalho": false,
    "estudos": false,
    "filmes": false
  }
}
```

### Rationale
Storing these configurations as simple key-value maps inside the database allows the UI to fetch them in a single query when the application loads or switches accounts. It also allows backend routes to easily determine whether to enforce separation filters on request queries.

### Alternatives Considered
- **Local Storage Only Configuration**: Storing configs purely on the frontend localStorage. Rejected because settings must persist across browsers and container recreations.
- **Embedded Config in User Documents**: Rejected because we are not using a password-based user/profile system; we are using two default local accounts.

---

## Decision 2: Active Account Context Passing

### Decision
The frontend will transmit the active account context via the HTTP header `X-Active-Account` (values: `car-j-works` or `car-j-home`).

### Rationale
Using a custom HTTP header is a standard practice for single-page applications communicating with REST APIs. It separates configuration context from URL paths and query parameters. In FastAPI, we can intercept this header globally using a Dependency:
```python
from fastapi import Header, HTTPException

def get_active_account(x_active_account: str = Header(default="car-j-home")):
    if x_active_account not in ["car-j-works", "car-j-home"]:
        raise HTTPException(status_code=400, detail="Invalid active account header")
    return x_active_account
```

### Alternatives Considered
- **Cookie-based profile transmission**: Can be blocked or altered, less explicit in developer-hub API design.
- **Query parameters (`?account=car-j-works`)**: Pollution of all GET/POST requests, harder to enforce consistently via middleware/dependencies.

---

## Decision 3: Transition Data Migration Strategy

### Decision
When changing sharing configuration, we migrate records in MongoDB by modifying their `account_id` tags:

1. **Shared to Separated**:
   - The user selects a target account to inherit the existing records (e.g., `car-j-works`).
   - The backend runs an update command on the target collection, setting `account_id = "car-j-works"` for all records that currently have no `account_id` or `account_id: null`.
   - Any new records created under the other account (`car-j-home`) will be saved with `account_id = "car-j-home"`.
   - Query filters check if the collection is separated: if so, query `{ account_id: active_account }`.

2. **Separated to Shared**:
   - The backend runs an update command on the target collection, unsetting or removing the `account_id` key (`{ "$unset": { "account_id": "" } }`) from all records of that category.
   - This merges the data by removing the ownership tag, making all items queryable by all accounts.

### Rationale
Directly modifying the documents in the DB ensures that no duplicate records are generated, and database storage remains clean. Query filters are extremely lightweight.

### Alternatives Considered
- **Data Duplication on Separation**: Copying shared data to both profiles. Rejected because it wastes database storage and creates sync issues if files are modified later.
- **Soft Association (Association Tables)**: Creating mapping documents. Rejected because it adds overhead to MongoDB's schema-less document structure.
