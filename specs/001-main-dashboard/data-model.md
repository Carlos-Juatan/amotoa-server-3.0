# Data Model: Main Dashboard & Account Switcher

This document details the MongoDB schemas and data entities supporting dashboard personalization and multi-account data isolation.

---

## 1. Entity: AccountConfiguration

### Collection
`accounts_config`

### Schema Representation (JSON / BSON)
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

### Attributes Description
- **`_id`**: String. Uniquely identifies the account. Must be one of `car-j-works` or `car-j-home`.
- **`visibility_settings`**: Object. A map of the 12 utility identifiers to boolean values. If `false`, the utility card is hidden from the dashboard view of the active account.
- **`data_separation_settings`**: Object. A map of the 12 utility identifiers to boolean values. If `true`, data in that utility's collection is isolated per account. If `false`, data is shared.

### Validation Rules
- `_id` must be exactly either `"car-j-works"` or `"car-j-home"`.
- `visibility_settings` and `data_separation_settings` must contain exactly the 12 designated keys: `series`, `animes`, `youtube`, `light_novels`, `manga`, `jogos`, `financas`, `saude_fitness`, `links`, `trabalho`, `estudos`, `filmes`. All values must be booleans.

---

## 2. Entity: GenericItem (Content Abstract Entity)

This model serves as the base structure for all content records across active utility modules (e.g. `links` collection, `finances` collection).

### Collection(s)
`links`, `series`, etc. (one collection per utility)

### Schema Representation (JSON / BSON)
```json
{
  "_id": {"$oid": "646b9a8f4c28f13488f28d8b"},
  "account_id": "car-j-works", 
  "created_at": "2026-05-23T13:00:00Z",
  "updated_at": "2026-05-23T13:00:00Z",
  "data": {
    "title": "Search Engine",
    "url": "https://google.com"
  }
}
```

### Attributes Description
- **`_id`**: ObjectId. Automatically generated unique identifier.
- **`account_id`**: String (optional). Set to the owning account ID (`car-j-works` or `car-j-home`) only when the utility's data separation is toggled to **Separated**. Unset or null when the utility is set to **Shared**.
- **`created_at`**: ISODate. Timestamp of record creation.
- **`updated_at`**: ISODate. Timestamp of last modification.
- **`data`**: Object. Freeform payload containing utility-specific details (e.g., links details, anime list status, financial items).

### Query Filtering Rules
Let `active_account` be the account identifier retrieved from the `X-Active-Account` header.
- **When item type `data_separation_settings[item_type]` is `false` (Shared)**:
  - Query: `{}` (Return all records, ignoring `account_id`).
- **When item type `data_separation_settings[item_type]` is `true` (Separated)**:
  - Query: `{ "account_id": active_account }` (Return only records owned by the active account).
