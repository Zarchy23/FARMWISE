# 🔒 FARMWISE - COMPLETE SECURITY & VALIDATION ARCHITECTURE

**Version:** 1.0  
**Last Updated:** April 4, 2026  
**Status:** In Implementation

---

## 📋 EXECUTIVE SUMMARY

FarmWise implements **defense in depth** - multiple layers of security working together to protect user data and system integrity. This document outlines the complete security architecture across 10 layers.

Think of it like securing a farm: fences, gates, locks, cameras, guards, and alarm systems. No single measure is enough.

---

## 1️⃣ AUTHENTICATION SECURITY (Who are you?)

### Password Security

#### Password Strength Requirements
- ✅ Minimum 12 characters (not 8)
- ✅ Must contain uppercase, lowercase, numbers, AND special characters
- ✅ Cannot be common password (no "password123", "admin2024", "farmwise")
- ✅ Cannot contain repeating characters (no "aaa", "111")
- ✅ Cannot contain keyboard patterns (no "qwerty", "123456")
- ✅ Cannot contain personal information (username, email, name)

#### Password History
- ✅ System remembers last 5 passwords per user
- ✅ Users cannot reuse any of last 5 passwords
- ✅ Password change required every 90 days

#### Account Lockout
- ✅ After 5 failed login attempts: lock for 15 minutes
- ✅ After 10 failed attempts in 1 hour: lock for 24 hours (admin unlock required)
- ✅ All failed attempts logged with IP address, timestamp, user agent

### Two-Factor Authentication (2FA)

#### TOTP Implementation
- ✅ Time-based One-Time Password (like Google Authenticator)
- ✅ QR code generated for user to scan with phone
- ✅ New 6-digit code generated every 30 seconds
- ✅ Code required to complete login after password

#### Backup Codes
- ✅ 10 one-time backup codes generated when enabling 2FA
- ✅ User stores codes securely (printed or saved)
- ✅ Each code usable once, regenerated after all used

### Email & Phone Verification

#### Email Verification
- ✅ Verification email sent on registration
- ✅ Unique link expires after 1 hour
- ✅ Some features locked until verified
- ✅ Resend option available

#### Phone Verification
- ✅ SMS with 6-digit code sent to phone
- ✅ Code expires after 5 minutes
- ✅ Prevents fake phone numbers

### Session Security

#### Implementation
- ✅ New session ID generated on every login
- ✅ Last IP address tracked per user
- ✅ Security alert sent for new IP logins
- ✅ Security alert sent for new device/browser
- ✅ Users can view and remotely log out other sessions
- ✅ Sessions expire after 24 hours of inactivity

---

## 2️⃣ AUTHORIZATION (What can you do?)

### Role-Based Access Control (RBAC)

| Role | Level | Access Scope |
|------|-------|--------------|
| System Admin | 100 | Everything - full system access |
| Cooperative Admin | 80 | All farms in cooperative |
| Large Farmer | 70 | Own farms + cooperative features |
| Agronomist | 60 | Assigned farms only |
| Equipment Owner | 50 | Own equipment listings |
| Farmer | 40 | Own farms only |
| Insurance Agent | 30 | Policies and claims |
| Market Trader | 30 | Marketplace only |
| Veterinarian | 30 | Animal health records |
| Viewer | 10 | Read-only access |

### Ownership Validation

**Every resource access must validate:**
- User owns the resource, OR
- User has explicit permission, OR
- User is admin with override permission

**Examples:**
- Farmer can only see own farms
- Cooperative admin sees all cooperative farms
- Agronomist assigned to farm sees only that farm
- Equipment owner only edits own listings

### Field-Level Security

| Data Type | Full Access | Masked For Others |
|-----------|-------------|-------------------|
| SSN/ID | Admin, Owner | ****1234 |
| Bank Account | Admin, Owner | ****5678 |
| Phone | Owner, Staff | +254******78 |
| Email | Owner, Admin | j***@example.com |

### API Security

- ✅ API key required (not just user login)
- ✅ Different rate limits by user type
- ✅ All API requests logged
- ✅ API keys individually revocable
- ✅ API keys expire after 90 days

---

## 3️⃣ INPUT VALIDATION (Is the data safe?)

### Threats Prevented

| Threat | Description | Impact |
|--------|-------------|--------|
| SQL Injection | Malicious code in queries | Data theft/deletion |
| XSS | JavaScript in pages | Session hijacking |
| Command Injection | System commands | Server takeover |
| Path Traversal | ../../../etc/passwd | File access |
| CSV Injection | Formulas in exports | Client malware |

### Validation by Field Type

#### Text Fields (Name, Description, Notes)
- ✅ Maximum length enforced
- ✅ Minimum length enforced
- ✅ HTML tags removed or escaped
- ✅ JavaScript removed entirely
- ✅ SQL keywords blocked (SELECT, DROP, INSERT, DELETE, UNION)
- ✅ Special characters limited/escaped
- ✅ No null bytes
- ✅ No control characters

#### Numeric Fields (Amount, Area, Weight)
- ✅ Minimum value validation
- ✅ Maximum value validation
- ✅ Decimal place limit (2 for currency)
- ✅ Type validation
- ✅ Range validation

#### Date Fields
- ✅ Cannot be in past where inappropriate
- ✅ Cannot be too far in future
- ✅ End date after start date
- ✅ Format validation (YYYY-MM-DD)

#### Email Fields
- ✅ Valid format (name@domain.tld)
- ✅ No disposable domains (mailinator.com)
- ✅ No role-based warnings (admin@, info@)
- ✅ MX record validation

#### Phone Fields
- ✅ International format with country code
- ✅ Valid country code
- ✅ No invalid numbers (0000000000)
- ✅ Length 9-15 digits after country code

#### File Uploads
- ✅ Type validation (check MIME, not just extension)
- ✅ Size limits (5MB images, 1MB documents)
- ✅ Filename sanitization
- ✅ Virus scanning
- ✅ Random filename storage

### Sanitization Process

Every input goes through:

1. **Trim** - Remove leading/trailing whitespace
2. **Strip** - Remove null bytes and control characters
3. **Escape** - Convert special characters to HTML entities
4. **Filter** - Remove dangerous patterns
5. **Validate** - Check against expected format
6. **Length limit** - Truncate if too long

---

## 4️⃣ FORM SECURITY

### CSRF Protection

- ✅ Every form has unique CSRF token
- ✅ Token validated before processing
- ✅ Token expires with session
- ✅ Token tied to user session

### Rate Limiting

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Login | 5 attempts | 15 minutes |
| Registration | 3 attempts | 1 hour |
| Password reset | 3 requests | 1 hour |
| Form submission | 50 | 1 hour |
| API (authenticated) | 1000 | 1 hour |
| API (unauthenticated) | 100 | 1 hour |
| File upload | 20 | 1 hour |

### Honeypot Fields

- ✅ Invisible field added to forms
- ✅ Hidden from real users with CSS
- ✅ Bots automatically fill
- ✅ Submission rejected if filled

### Form Validation Order

1. CSRF token validation
2. Rate limit check
3. Honeypot check
4. Required fields check
5. Data type validation
6. Format validation
7. Range validation
8. Business logic validation
9. Database constraint validation

---

## 5️⃣ DATABASE SECURITY

### Encryption

#### At Rest
- ✅ Database files encrypted on disk
- ✅ Backup files encrypted
- ✅ Sensitive fields encrypted (API keys, tokens)

#### In Transit
- ✅ All connections use TLS/SSL
- ✅ Certificate validation enabled
- ✅ No unencrypted connections

### Query Security

- ✅ Always use parameterized queries
- ✅ Never execute raw user input as SQL
- ✅ Query result size limit (1000 rows max)
- ✅ Query timeout (30 seconds)

### Data Integrity

- ✅ Foreign key constraints
- ✅ Unique constraints
- ✅ Check constraints
- ✅ Not null constraints where appropriate

### Audit Trail

Every CREATE, UPDATE, DELETE logged with:
- User ID who performed action
- Timestamp
- What was changed (old → new value)
- IP address
- User agent

---

## 6️⃣ API SECURITY

### Authentication Methods

- ✅ Bearer token (JWT) - mobile apps
- ✅ API key - third-party integrations
- ✅ Session cookie - web app

### Request Validation

Every request validated for:
- ✅ Authentication present and valid
- ✅ Authorization (has permission)
- ✅ Rate limit not exceeded
- ✅ Request size within limits (10MB max)
- ✅ Content-Type correct
- ✅ Accept header supported

### Response Security Headers

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: same-origin
Content-Security-Policy: [policy]
```

### Error Handling

**User sees:** "An error occurred. Our team has been notified."

**Logged internally:**
- Full stack trace
- Database query
- User input
- Timestamp
- Request ID

---

## 7️⃣ FILE UPLOAD SECURITY

### Validation Checklist

| Check | Prevents |
|-------|----------|
| Extension whitelist | .exe, .php, .js, .html |
| MIME verification | Fake extensions |
| Size limit | DoS attacks |
| Magic bytes check | File type spoofing |
| Virus scan | Malware |
| Filename sanitization | Path traversal |

### Allowed File Types

| Use Case | Types | Max Size |
|----------|-------|----------|
| Profile pictures | JPG, PNG, GIF | 2MB |
| Product images | JPG, PNG, WEBP | 5MB |
| Documents | PDF, DOC, DOCX | 10MB |
| Receipts | PDF, JPG, PNG | 5MB |
| Pest photos | JPG, PNG | 10MB |

### Storage Security

- ✅ Random generated filenames (never user-provided)
- ✅ Stored outside web root
- ✅ Access controlled through auth endpoints
- ✅ Virus scanning before storage
- ✅ Temp file auto-deletion

---

## 8️⃣ PAYMENT SECURITY (PCI Compliance)

### Card Data Handling

- ✅ Never touch raw card numbers (use Stripe.js)
- ✅ Form submits directly to Stripe
- ✅ Receive payment token, not card number
- ✅ Store only last 4 digits and expiry
- ✅ Use PCI-compliant iframe

### Transaction Validation

- ✅ Amount validation (positive, within limits)
- ✅ Currency validation
- ✅ Duplicate transaction detection
- ✅ Webhook signature verification
- ✅ Idempotency keys (prevent double charging)

### Compliance

- ✅ Encrypt cardholder data in transit (TLS 1.2+)
- ✅ Never store full card numbers or CVV
- ✅ Tokenization for card replacement
- ✅ Regular security scans
- ✅ Access logs for all payment systems

---

## 9️⃣ LOGGING & MONITORING

### Security Events (ALWAYS log)

- ✅ Login attempts (success/failure)
- ✅ Password changes
- ✅ 2FA enable/disable
- ✅ Permission changes
- ✅ API key creation/revocation
- ✅ Admin actions
- ✅ Data exports
- ✅ Account deletion

### Application Events

- ✅ Form validation failures
- ✅ Database errors
- ✅ API errors
- ✅ Slow queries (>1 sec)
- ✅ File uploads

### Never Log

- ❌ Passwords (any form)
- ❌ Credit card numbers
- ❌ Full SSN/ID numbers
- ❌ Authentication tokens
- ❌ Session IDs in plain text
- ❌ Health information

### Alert Triggers

| Event | Action |
|-------|--------|
| 10+ failed logins/1 min | Block IP, notify admin |
| Password from new IP | Email user confirmation |
| Export >1000 records | Admin review required |
| Admin login new location | SMS to backup admin |
| API key used from new country | Flag for review |

---

## 🔟 DATA PRIVACY (GDPR/CCPA)

### User Rights

| Right | Implementation |
|-------|----------------|
| Access | Download all data as JSON/CSV |
| Correct | Edit profile and fields |
| Delete | Account deletion with grace period |
| Export | One-click export |
| Withdraw | Toggle preferences |
| Object | Opt-out of marketing |

### Data Retention Policy

| Data Type | Retention | After Expiry |
|-----------|-----------|-------------|
| User account | Until deletion | Anonymized (30 days) |
| Transactions | 7 years | Archived |
| Audit logs | 2 years | Deleted |
| Crop records | 5 years | Aggregated |
| Chat messages | 1 year | Deleted |
| Session data | 30 days | Deleted |
| Failed logins | 90 days | Deleted |

### Data Minimization

- ✅ Collect only what's needed
- ✅ No SSN unless required for payments
- ✅ No birth date unless age verification needed
- ✅ No location tracking unless mapping
- ✅ Allow anonymous usage where possible

---

## 📊 CRITICAL IMPLEMENTATION CHECKLIST

See `SECURITY_IMPLEMENTATION_CHECKLIST.md` for detailed implementation progress.

### Critical (Do Now)

- [ ] Enforce strong password policy (12+ chars, complexity)
- [ ] Implement account lockout (5 attempts)
- [ ] Add CSRF protection (all forms)
- [ ] Sanitize all inputs (XSS protection)
- [ ] Use parameterized queries (SQL injection)
- [ ] Add rate limiting
- [ ] Implement audit logging
- [ ] Add security headers
- [ ] Validate file uploads
- [ ] Encrypt sensitive data

---

## ✅ IMMEDIATE ACTIONS

1. **Add CSRF tokens** - `{% csrf_token %}` in all forms
2. **Enable HTTPS** - Let's Encrypt (free)
3. **Set DEBUG=False** - Production only
4. **Change admin URL** - From `/admin/` to custom
5. **Add rate limiting** - Per endpoint
6. **Configure logging** - To file, not console
7. **Set secure cookies** - `SESSION_COOKIE_SECURE=True`
8. **Add security headers** - HSTS, CSP, X-Frame-Options
9. **Validate file uploads** - Don't trust filenames
10. **Add account lockout** - After failed logins

---

## 🎯 PRIORITY IMPLEMENTATION ORDER

**Phase 1 (Critical - This Week):**
1. Strong password enforcement
2. Account lockout mechanism
3. Input validation & sanitization
4. Parameterized queries
5. CSRF protection
6. Security headers
7. Audit logging

**Phase 2 (High - This Month):**
1. Email verification
2. Phone verification
3. Rate limiting
4. Session timeout
5. RBAC enforcement
6. Ownership validation
7. File upload validation

**Phase 3 (Medium - Next Month):**
1. Two-factor authentication
2. Password history
3. IP-based alerts
4. Data retention policies
5. GDPR export
6. API key authentication
7. Webhook verification

---

## 📖 RELATED FILES

- `SECURITY_IMPLEMENTATION_CHECKLIST.md` - Detailed implementation tracking
- `core/validators.py` - Input validation functions (to be created)
- `core/middleware.py` - Security middleware (to be created)
- `docs/SECURITY_GUIDE.md` - Admin security guide (to be created)

---

## 🔐 SECURITY CONTACT

For security issues, report to: `security@farmwise.local`

**Do NOT report security issues as public GitHub issues.**

---

**Last Updated:** April 4, 2026  
**Next Review:** July 4, 2026
