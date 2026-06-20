# Getting Started & Onboarding FAQ

## What is this platform?

Our platform provides a unified API gateway for businesses to integrate AI-powered features into their products. It includes natural language processing, computer vision, and data analytics capabilities accessible through a single REST API.

---

## How do I get started?

### Step 1: Create an Account
Visit app.example.com/signup and register using your work email.
A verification email will be sent — click the link within 24 hours.

### Step 2: Explore the Dashboard
Your dashboard shows:
- API usage statistics
- Active services and integrations
- Recent activity logs
- Quick-start tutorials

### Step 3: Generate Your First API Key
1. Go to Settings > API Keys > Create New Key
2. Name it "My First Key"
3. Select "All Scopes" for initial testing
4. Copy and save your key

### Step 4: Make Your First API Call
```bash
curl -X GET "https://api.example.com/v1/status" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Expected response:
```json
{
  "status": "ok",
  "version": "2.5.1",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Step 5: Explore Our Quickstart Guides
Find language-specific guides in our Documentation:
- Python SDK: `pip install example-sdk`
- Node.js SDK: `npm install @example/sdk`
- Java SDK: Available via Maven Central

---

## Frequently Asked Questions

### Q: How long does account verification take?
The verification email is sent instantly. Check your spam folder if not received within 5 minutes. Links expire after 24 hours — request a new one at app.example.com/resend-verification.

### Q: Can I use a personal email to sign up?
Yes, but Enterprise features require a work email domain. Free and Pro plans accept any valid email.

### Q: How many team members can I invite?
- Free Plan: 1 user (owner only)
- Pro Plan: Up to 10 team members
- Enterprise Plan: Unlimited team members

### Q: Is there a free trial for paid plans?
Yes! Pro Plan includes a 14-day free trial. No credit card required.
Enterprise plan includes a 30-day proof-of-concept period with dedicated support.

### Q: What happens if I exceed my API limit?
- Free Plan: Requests return a 429 error until the next day
- Pro Plan: You can enable "burst credits" at $0.001 per additional call
- Enterprise Plan: Automatic scaling with negotiated overage rates

### Q: Where is my data stored?
- Default: US-East (Virginia)
- EU customers can request EU-West (Ireland) storage
- Enterprise customers can specify their preferred region

### Q: How do I integrate with my existing tools?
We offer native integrations with:
- Zapier (no-code automation)
- Make (formerly Integromat)
- Slack (notifications and alerts)
- Jira and GitHub (developer workflows)
- Salesforce and HubSpot (CRM)
- Find all integrations at app.example.com/integrations

### Q: What support channels are available?
- Free Plan: Community forum at community.example.com
- Pro Plan: Email support at support@example.com (24-48 hour response)
- Enterprise Plan: 24/7 phone, email, and dedicated Slack channel

### Q: How do I cancel my subscription?
Go to Settings > Billing > Cancel Plan. Your access continues until the end of the billing period. No cancellation fees.

### Q: Can I export my data?
Yes. Go to Settings > Data > Export. Available formats: JSON, CSV, XML.
Large exports are processed asynchronously and emailed as a download link within 1-4 hours.

---

## Service Status and Incident Communication

Monitor real-time platform status at status.example.com.

Subscribe to incident notifications:
1. Visit status.example.com
2. Click "Subscribe to Updates"
3. Choose email, SMS, or RSS feed

Our incident response process:
1. Detection (automated monitoring, <5 min)
2. Acknowledgment (posted to status page, <15 min)
3. Investigation and mitigation
4. Resolution and post-mortem (published within 48 hours)

---

## Contacting Support

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| Technical bugs | support@example.com | 24-48 hours (Pro) |
| Billing questions | billing@example.com | 2-3 business days |
| Security concerns | security@example.com | 4 hours |
| Sales inquiries | sales@example.com | Same business day |
| Legal/Compliance | legal@example.com | 5 business days |
| Urgent (Enterprise) | +1-800-555-0199 | Immediate |
