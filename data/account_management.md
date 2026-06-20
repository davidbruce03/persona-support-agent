# Account Management & Security Guide

## User Roles and Permissions

### Role Hierarchy

| Role | Dashboard | API Access | Billing | User Management |
|------|-----------|-----------|---------|-----------------|
| Viewer | Read Only | None | None | None |
| Developer | Read/Write | Full | View | None |
| Admin | Full | Full | Full | Add/Remove |
| Owner | Full | Full | Full | Full + Transfer |

To change a user's role:
1. Go to Settings > Team Members
2. Click the user's name
3. Select new role from the dropdown
4. Click "Save Changes"
The user will receive an email notification of their role change.

---

## Multi-Factor Authentication (MFA)

### Enabling MFA (Strongly Recommended)
1. Go to Settings > Security > Two-Factor Authentication
2. Choose your MFA method:
   - **Authenticator App** (recommended): Google Authenticator, Authy, or 1Password
   - **SMS**: A 6-digit code sent to your registered phone number
   - **Hardware Key**: YubiKey or FIDO2-compatible device
3. Follow the on-screen setup wizard
4. Save your 10 backup codes in a secure location

### MFA Recovery
If you lose access to your MFA device:
1. Use one of your saved backup codes on the login screen
2. If backup codes are lost, contact security@example.com from your registered email
3. Identity verification may be required (government ID for Enterprise accounts)

---

## SSO (Single Sign-On) Configuration

### Supported Providers
- Google Workspace
- Microsoft Azure AD / Entra ID
- Okta
- OneLogin
- Any SAML 2.0 compliant identity provider

### Setup Process (Admin Only)
1. Navigate to Settings > Security > SSO Configuration
2. Select your identity provider
3. Download our Service Provider metadata XML
4. Upload it to your IdP and configure the SAML assertion
5. Enter your IdP's metadata URL in our dashboard
6. Test the connection using the "Test SSO" button
7. Enable SSO enforcement for all team members (optional but recommended)

---

## Data Privacy and Compliance

### GDPR Compliance
We are fully GDPR compliant. For EU customers:
- Data is stored in EU-West (Ireland) data centers by default
- Data Processing Agreement (DPA) available at legal@example.com
- Right to erasure requests processed within 30 days
- Data portability: Export all your data at Settings > Data > Export

### HIPAA Compliance
Available for Enterprise plans with a signed Business Associate Agreement (BAA).
Contact sales@example.com to initiate the BAA process.

### SOC 2 Type II
Our platform is SOC 2 Type II certified. Audit reports available upon request under NDA.

---

## Account Deletion and Data Retention

### How to Delete Your Account
1. Ensure you have exported any data you need (Settings > Data > Export)
2. Cancel your subscription (Settings > Billing > Cancel Plan)
3. Go to Settings > Account > Delete Account
4. Enter your password and confirm deletion
5. You will receive a confirmation email

**Warning:** Account deletion is permanent. All data, API keys, and configurations will be permanently erased after the 90-day retention window.

### Data Retention Schedule
| Data Type | Retention Period |
|-----------|-----------------|
| API logs | 90 days |
| Billing records | 7 years (legal requirement) |
| User data | 90 days after account deletion |
| Backups | 30 days rolling |

---

## Session Management

### Active Sessions
View and revoke active sessions at Settings > Security > Active Sessions.
Each session shows:
- Device type and browser
- IP address and approximate location
- Last active timestamp

### Automatic Session Timeout
- Free/Pro accounts: Sessions expire after 30 days of inactivity
- Enterprise accounts: Configurable (1 hour to 90 days)
- Force logout all sessions: Settings > Security > Revoke All Sessions

---

## API Key Management

### Best Practices
- Never commit API keys to version control (use `.env` files)
- Create separate keys for development and production environments
- Set key expiration dates for enhanced security
- Use the minimum required scopes for each key

### Creating a New API Key
1. Go to Settings > API Keys > Create New Key
2. Enter a descriptive name (e.g., "Production Backend - Jan 2025")
3. Select required scopes
4. Set an optional expiration date
5. Copy and securely store the key immediately — it will not be shown again

### Rotating a Compromised Key
If you suspect your API key has been exposed:
1. Immediately go to Settings > API Keys
2. Click "Revoke" next to the compromised key
3. Generate a new key and update all services
4. Review API logs at Settings > API Keys > Usage Logs for unauthorized activity
5. Report security concerns to security@example.com
