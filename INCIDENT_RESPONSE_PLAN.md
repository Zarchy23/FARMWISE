# 🚨 FarmWise Incident Response Plan & Procedures

**Version:** 2.0  
**Last Updated:** April 11, 2026  
**Status:** ACTIVE  
**Responsibility:** Security Team

---

## 📋 INCIDENT SEVERITY CLASSIFICATION

### CRITICAL 🔴
- **Impact:** System unavailable or data breach
- **Response Time:** 15 minutes
- **Examples:**
  - Ransomware detected
  - Database compromised
  - All servers down
  - Data exfiltration suspected
  - Unauthorized admin access

**Actions:**
1. Activate full incident team
2. Isolate affected systems
3. Notify management immediately
4. Preserve evidence
5. Begin recovery procedures

---

### HIGH 🟠
- **Impact:** Service degraded or security event
- **Response Time:** 1 hour
- **Examples:**
  - Unauthorized user access
  - DDoS attack active
  - SSL certificate issues
  - Backup failure (2+ consecutive)
  - Suspicious admin activity

**Actions:**
1. Begin investigation
2. Document findings
3. Take containment measures
4. Update status
5. Notify stakeholders

---

### MEDIUM 🟡
- **Impact:** Minor security issue or warning
- **Response Time:** 4 hours
- **Examples:**
  - Failed login spike
  - Suspicious user behavior
  - Backup slightly delayed
  - Certificate expiring soon (> 14 days)
  - API error rate elevated

**Actions:**
1. Monitor closely
2. Investigate trends
3. Document incident
4. Plan remediation
5. Follow up daily

---

### LOW 🟢
- **Impact:** Information only
- **Response Time:** 1 day
- **Examples:**
  - Certificate expiring (> 30 days)
  - Disk space normal but trending high
  - Log file rotation
  - Routine maintenance
  - Policy updates

**Actions:**
1. Log incident
2. Schedule resolution
3. Update documentation

---

## 🔍 INCIDENT RESPONSE WORKFLOW

### Phase 1: DETECTION (0-10 min)

**Who discovers:**
- Automated monitoring alerts
- User reports
- Routine checks
- Log analysis

**First responder actions:**
```
□ Acknowledge alert/report
□ Verify issue is real (not false alarm)
□ Determine severity level
□ Notify incident commander
□ Document initial findings
□ Start incident timeline
```

**Key questions:**
- What is the scope? (1 user? All users? Production?)
- When did it start?
- Who reported it?
- What's the current impact?

---

### Phase 2: CONTAINMENT (10-60 min)

#### For Data Breach:
```
✓ STOP: Don't shut down (preserve evidence)
✓ ISOLATE: Take affected server offline
✓ PRESERVE: Copy logs before deleting
✓ NOTIFY: Alert incident commander
✓ DOCUMENT: What we found, when we found it
```

**Commands (Linux):**
```bash
# Preserve logs before bringing down
sudo tar -czf /backups/incident_evidence_$(date +%s).tar.gz /var/log/

# Take service offline
sudo systemctl stop django
sudo systemctl stop redis
sudo systemctl stop postgresql

# Notify team
echo "INCIDENT ALERT" | mail -s "PRODUCTION DOWN" security-team@farmwise.com
```

#### For Unauthorized Access:
```bash
# IMMEDIATELY revoke all sessions
python manage.py shell << 'EOF'
from django.contrib.sessions.models import Session
Session.objects.all().delete()
print("All sessions terminated")
EOF

# Force password resets for admins
python manage.py shell << 'EOF'
from core.models import User
admins = User.objects.filter(is_staff=True)
for admin in admins:
    admin.set_unusable_password()
    admin.save()
print(f"Reset password for {admins.count()} admins")
EOF
```

#### For DDoS Attack:
```
□ Enable rate limiting (if not already)
□ Block offending IPs
□ Activate Cloudflare/WAF
□ Notify infrastructure team
□ Monitor traffic patterns
```

---

### Phase 3: INVESTIGATION (30-120 min)

**Security Officer checks:**

1. **Who accessed what?**
```bash
# Review access logs
grep "UNAUTHORIZED\|ERROR" /var/log/farmwise/security.log | tail -100

# Check file modifications
find / -type f -newermt "2 hours ago" 2>/dev/null | grep -v /proc

# Review database queries
SELECT * FROM core_models.loginattempt 
WHERE timestamp > NOW() - INTERVAL 2 HOUR 
ORDER BY timestamp DESC;
```

2. **When did it happen?**
```bash
# Timeline of events
grep -h "timestamp" /var/log/farmwise/*.log | sort | tail -50
```

3. **How did they get access?**
```bash
# Check for vulnerabilities
python manage.py check --deploy

# Review nginx/access logs
tail -100 /var/log/nginx/access.log | grep -i "sql\|<script\|admin"
```

4. **What was compromised?**
```bash
# Check database integrity
SELECT COUNT(*) FROM core_models.user WHERE is_staff = TRUE;
SELECT * FROM core_models.user WHERE last_login > NOW() - INTERVAL 1 HOUR;

# Verify backups integrity
gunzip -t /backups/farmwise/farmwise_db_*.sql.gz
```

---

### Phase 4: ERADICATION (1-4 hours)

#### Patch Vulnerability:
```bash
# Identify vulnerable code
git log --grep="security" --oneline | head -20

# Apply security patch
git pull origin main
python manage.py migrate
python manage.py check --deploy
systemctl restart django
```

#### Remove Attacker Access:
```bash
# Disable compromised accounts
python manage.py shell << 'EOF'
from core.models import User
User.objects.filter(username='attacker').update(is_active=False)
print("Compromised account disabled")
EOF

# Reset API keys
python manage.py shell << 'EOF'
from core.models import APIKey
APIKey.objects.all().delete()
print("All API keys reset")
# Users must regenerate
EOF

# Revoke cookies/sessions
from django.contrib.sessions.models import Session
Session.objects.all().delete()
```

#### Enhanced Security:
```python
# Update password hash
from django.contrib.auth.hashers import make_password
admin = User.objects.get(username='admin')
admin.password = make_password('NEW_STRONG_PASSWORD')
admin.save()

# Force 2FA re-enrollment
admin.totp_device.delete()
# Admin must re-register 2FA
```

---

### Phase 5: RECOVERY (30 min - 4 hours)

#### Option 1: Full Restore from Backup
```bash
# Stop services
sudo systemctl stop django

# Restore database
python manage.py shell << 'EOF'
from core.backup_manager import BackupManager
manager = BackupManager()
# Get last known-good backup (before incident)
manager.restore_database('/backups/farmwise/farmwise_db_20260410_020000.sql.gz')
EOF

# Restart services
sudo systemctl start django
sudo systemctl restart redis
```

#### Option 2: Patch and Verify
```bash
# Apply security patches
git pull origin security-hotfix

# Run migrations
python manage.py migrate

# Verify application
python manage.py check --deploy

# Restart services
sudo systemctl restart django
```

#### Verification Checklist:
```
□ Application responds to requests
□ Authentication working (can log in)
□ Database queries working
□ Backups still running
□ Monitoring/alerts active
□ SSL certificate valid
□ All services running
□ No error logs spike
□ Users can access data
□ No data corruption detected
```

---

### Phase 6: POST-MORTEM (Within 48 hours)

**Document:**
```markdown
## Incident Report: [TITLE]

**Incident ID:** [Auto-generated]
**Date:** [When it occurred]
**Duration:** [Start to end]
**Severity:** [CRITICAL/HIGH/MEDIUM/LOW]

### Timeline:
- T+0:00 - [What happened]
- T+0:15 - [What we did]
- T+1:00 - [Incident contained]
- T+2:00 - [Recovered]

### Root Cause:
[Explain what actually caused it]

### Impact:
- [Number of users affected]
- [Duration of service down]
- [Data affected]

### Remediation:
1. [What we did to fix]
2. [How we prevented recurrence]
3. [Timeline for implementation]

### Lessons Learned:
[What to improve for next time]
```

**Follow-up Actions:**
- [ ] Fix root cause
- [ ] Update security
- [ ] Train team
- [ ] Update procedures
- [ ] Post-mortem meeting
- [ ] Status update to users
- [ ] News/communications

---

## 🚨 EMERGENCY CONTACTS

| Role | Name | Phone | Email |
|------|------|-------|-------|
| Incident Commander | [Name] | [Phone] | [Email] |
| Security Officer | [Name] | [Phone] | [Email] |
| Database Admin | [Name] | [Phone] | [Email] |
| Infrastructure Lead | [Name] | [Phone] | [Email] |
| CTO | [Name] | [Phone] | [Email] |
| Legal/Compliance | [Name] | [Phone] | [Email] |

**On-call Rotation:**
- Week 1: [Name]
- Week 2: [Name]
- Week 3: [Name]
- Week 4: [Name]

---

## 📞 ESCALATION CHAIN

```
Detection
   ↓
On-Call Engineer (decides severity)
   ↓
IF HIGH/CRITICAL: → Activate full incident team
                   → Contact CTO
                   → Alert all stakeholders
   ↓
IF LEGAL ISSUE:   → Notify legal department
                   → Prepare disclosure if needed
   ↓
IF FINANCIAL:     → Alert finance
                   → Document costs
   ↓
IF PUBLIC:        → Prepare press statement
                   → Coordinate communication
```

---

## 💬 COMMUNICATION TEMPLATES

### To Users (Service Down):
```
Subject: URGENT: FarmWise Service Temporarily Down

We're experiencing a temporary service disruption and are 
working to restore access as quickly as possible.

Status: Investigating
ETA: [Time]
Updates: status.farmwise.com
```

### To Users (Security Incident):
```
Subject: Security Incident - Action may be required

We detected unauthorized access to [service].
What happened: [Brief description]
Your action: [What users need to do]
Details: [Link to blog post]
```

### To Team (Incident Start):
```
🚨 INCIDENT ALERT

Severity: HIGH
Type: [Type]
Status: INVESTIGATING
Commander: [Name]

Details: [Slack thread with updates]
```

### To Team (All Clear):
```
✓ INCIDENT RESOLVED

Duration: [Hours/minutes]
Resolution: [What we did]
Follow-up: [Meetings/updates]
```

---

## 🛡️ INCIDENT PREVENTION CHECKLIST

**After each incident, review:**

- [ ] Could monitoring have detected it sooner?
- [ ] Did we have backups available?
- [ ] Was access control sufficient?
- [ ] Were logs adequate for investigation?
- [ ] Could automation have prevented it?
- [ ] Do we need additional tools?
- [ ] Should we update procedures?
- [ ] What's the permanent fix?
- [ ] How do we train team?
- [ ] When do we drill again?

---

## 🔄 QUARTERLY INCIDENT DRILLS

**Scheduled:**
- Q1: Ransomware recovery drill
- Q2: Data breach response drill
- Q3: DDoS mitigation drill
- Q4: Full disaster recovery drill

**Each drill includes:**
1. Simulated incident triggered
2. Team mobilizes and investigates
3. Recovery procedures executed
4. Debrief and lessons learned
5. Procedures updated based on findings

---

## 📋 CHECKLIST: Ready for Incidents?

- [ ] Contact list complete and tested
- [ ] Incident procedures documented
- [ ] Recovery procedures tested (within 90 days)
- [ ] Backups verified (within 30 days)
- [ ] Disaster recovery plan updated
- [ ] Team trained on procedures
- [ ] Monitoring and alerts active
- [ ] Logging enabled on all systems
- [ ] Communication templates ready
- [ ] Legal/compliance aligned
- [ ] Insurance policy reviewed
- [ ] Status page configured

---

**See also:**
- `SECURITY_HARDENING_PLAN.md` - Prevention measures
- `BACKUP_AND_SECURITY_SETUP.md` - Backup procedures
- `SECURITY.md` - Security features
- Incident Tracking Board: [Link to Jira/GitHub Issues]

**Last Drill:** [Date]  
**Next Drill:** [Date]  
**Owner:** Security Team  
**Review Frequency:** Quarterly
