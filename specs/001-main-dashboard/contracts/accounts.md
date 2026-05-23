# API Contract: Accounts & Config Management

All requests interacting with account-specific logic must include the custom header `X-Active-Account` (value must be either `car-j-works` or `car-j-home`).

---

## 1. Get All Accounts Configurations

Retrieves visibility and data sharing settings for all accounts.

* **URL**: `/api/accounts/config`
* **Method**: `GET`
* **Headers**:
  * `X-Active-Account`: `car-j-works` | `car-j-home`
* **Response Status**: `200 OK`
* **Response Body**:
```json
{
  "car-j-works": {
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
  },
  "car-j-home": {
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
}
```

---

## 2. Update Account Configurations & Migrate Data

Updates visibility and/or sharing toggles for a specific account. If a utility's sharing toggle changes state, this endpoint handles the migration/merge of existing records.

* **URL**: `/api/accounts/config`
* **Method**: `PUT`
* **Headers**:
  * `X-Active-Account`: `car-j-works` | `car-j-home`
  * `Content-Type`: `application/json`
* **Request Body**:
```json
{
  "account_id": "car-j-works",
  "visibility_settings": {
    "series": true,
    "animes": true,
    "youtube": false, 
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
    "links": true, 
    "trabalho": false,
    "estudos": false,
    "filmes": false
  },
  "transition_options": {
    "links": {
      "action": "separate", 
      "inherit_account_id": "car-j-works" 
    }
  }
}
```

### Request Payload Details
- **`account_id`**: String. The identifier of the account being configured.
- **`visibility_settings`**: Object. Updated visibility map.
- **`data_separation_settings`**: Object. Updated sharing map.
- **`transition_options`**: Object (optional). Maps utility ID (e.g. `links`) to transition actions if a sharing status is changing:
  - **If transitioning from Shared to Separated**:
    - `action` must be `"separate"`.
    - `inherit_account_id` specifies which account inherits all existing records (`car-j-works` or `car-j-home`).
  - **If transitioning from Separated to Shared**:
    - `action` must be `"merge"`. No `inherit_account_id` needed since records are merged.

* **Response Status**: `200 OK`
* **Response Body**:
```json
{
  "status": "success",
  "message": "Account configuration updated and data transitioned successfully."
}
```
* **Error Response Status**: `400 Bad Request` (e.g., if transitioning to separated but `inherit_account_id` is missing/invalid).
