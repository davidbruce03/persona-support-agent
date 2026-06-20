# API Troubleshooting Guide

## Authentication Errors

### 401 Unauthorized
A 401 error means your API key is missing, invalid, or expired.

**Root Cause Analysis:**
- The `Authorization` header is not being sent correctly
- The Bearer token has expired (tokens expire after 24 hours by default)
- The API key has been revoked from the developer dashboard

**Resolution Steps:**
1. Verify your request includes the correct header: `Authorization: Bearer YOUR_API_KEY`
2. Regenerate your API key from Settings > API Keys > Rotate Key
3. Ensure the key has the required scopes: `read`, `write`, `admin`
4. Check your account is not suspended due to billing issues

**Code Example (Python):**
```python
import requests

headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
response = requests.get("https://api.example.com/v1/data", headers=headers)
```

### 403 Forbidden
You are authenticated but lack permission for this resource.

**Resolution:**
- Contact your organization admin to upgrade your role to `developer` or `admin`
- Check IP whitelisting settings in Security > Access Control
- Verify the endpoint is included in your plan tier

---

## Rate Limiting (429 Too Many Requests)

Our API enforces the following limits:

| Plan | Requests/min | Requests/day |
|------|-------------|-------------|
| Free | 60 | 1,000 |
| Pro | 1,000 | 50,000 |
| Enterprise | Unlimited | Unlimited |

**Resolution:**
- Implement exponential backoff with jitter
- Cache responses where possible
- Use batch endpoints for bulk operations
- Upgrade your plan at Billing > Upgrade Plan

**Retry Logic Example:**
```python
import time
import random

def api_call_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            wait = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait)
        else:
            return response
    raise Exception("Max retries exceeded")
```

---

## Webhook Configuration

### Webhook Not Receiving Events
1. Ensure your endpoint returns HTTP 200 within 5 seconds
2. Check the webhook secret is correctly validated using HMAC-SHA256
3. Review delivery logs at Dashboard > Webhooks > Event Logs
4. Whitelist our IP range: `52.74.0.0/16` and `34.87.0.0/16`

### Webhook Signature Validation
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## Database Integration Errors

### Connection Timeout
- Default connection timeout is 30 seconds
- Increase timeout in config: `DB_TIMEOUT=60`
- Check firewall rules allow outbound port 5432 (PostgreSQL) or 27017 (MongoDB)
- Use connection pooling to avoid repeated handshakes

### SSL Certificate Errors
```bash
# Test SSL connection
openssl s_client -connect your-db-host:5432 -starttls postgres

# Common fix: update CA certificates
sudo apt-get update && sudo apt-get install ca-certificates
```

---

## SDK Error Codes Reference

| Code | Meaning | Action |
|------|---------|--------|
| E1001 | Invalid payload schema | Validate JSON against API schema |
| E1002 | Missing required field | Check required fields in docs |
| E2001 | Resource not found | Verify resource ID exists |
| E3001 | Internal server error | Retry after 60 seconds; contact support if persistent |
| E4001 | Service unavailable | Check status.example.com for outages |
