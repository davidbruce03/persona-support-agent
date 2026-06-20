# Performance, Uptime & SLA Documentation

## Service Level Agreements

### Uptime Commitments

| Plan | Monthly Uptime SLA | Maximum Downtime/Month |
|------|-------------------|------------------------|
| Free | No SLA | N/A |
| Pro | 99.9% | ~43 minutes |
| Enterprise | 99.99% | ~4.3 minutes |

Uptime is calculated monthly using the formula:
Uptime % = ((Total Minutes - Downtime Minutes) / Total Minutes) × 100

Scheduled maintenance windows are excluded from SLA calculations and announced at least 72 hours in advance via status.example.com.

---

## API Performance Benchmarks

### Latency Targets (p95)

| Endpoint Type | Target Latency | Maximum Allowed |
|--------------|---------------|-----------------|
| Authentication | < 100ms | 500ms |
| Read operations | < 200ms | 1000ms |
| Write operations | < 300ms | 2000ms |
| AI inference | < 1500ms | 5000ms |
| Batch operations | < 5000ms | 30000ms |

### Response Time Monitoring
Real-time latency metrics are available at:
- Dashboard > Analytics > Performance
- API endpoint: GET /v1/metrics/latency
- Grafana dashboard (Enterprise only): grafana.example.com

---

## Infrastructure and Redundancy

### Data Center Architecture
- **Primary**: US-East-1 (Virginia, AWS)
- **Failover**: US-West-2 (Oregon, AWS)
- **EU Region**: EU-West-1 (Ireland, AWS)
- **APAC Region**: AP-Southeast-1 (Singapore, AWS)

### Redundancy Features
- Multi-AZ database deployment with automatic failover (<30 seconds)
- CDN distribution via Cloudflare (100+ edge locations)
- Load balancing across minimum 3 active application servers
- Database backups every 6 hours with point-in-time recovery

---

## Incident Classification and Response

### Severity Levels

**P0 - Critical (Full Outage)**
- Definition: Complete service unavailability affecting all customers
- Response Time: 15 minutes
- Resolution Target: 2 hours
- Communication: Status page updated every 15 minutes

**P1 - High (Major Degradation)**
- Definition: Core functionality impaired, affecting >50% of customers
- Response Time: 30 minutes
- Resolution Target: 4 hours
- Communication: Status page updated every 30 minutes

**P2 - Medium (Partial Degradation)**
- Definition: Non-core feature unavailable or performance degraded
- Response Time: 2 hours
- Resolution Target: 24 hours
- Communication: Status page updated every 2 hours

**P3 - Low (Minor Issue)**
- Definition: Edge case bugs or minor performance issues
- Response Time: 1 business day
- Resolution Target: 5 business days
- Communication: Release notes

---

## Business Impact of Downtime

### Calculating Operational Impact

For Enterprise customers, our team provides:
1. **Real-time business impact assessment** during P0/P1 incidents
2. **Estimated revenue impact calculator** based on your API usage patterns
3. **Workaround recommendations** to minimize operational disruption

### SLA Credit Request Process

1. Identify the incident on status.example.com and note the Incident ID
2. Calculate downtime using our formula:
   Eligible downtime = Total incident duration - scheduled maintenance windows
3. Submit credit request within 30 days:
   - Email: sla-credits@example.com
   - Subject: "SLA Credit Request - [Incident ID] - [Account ID]"
4. Credits are reviewed within 5 business days
5. Approved credits appear on your next invoice

### Credit Schedule

| Monthly Uptime | Credit (% of Monthly Fee) |
|---------------|--------------------------|
| 99.0% - 99.9% | 10% |
| 95.0% - 99.0% | 25% |
| < 95.0% | 50% |

Maximum credit per month: 50% of monthly fee.
Credits are non-transferable and cannot be converted to cash.

---

## Disaster Recovery

### Recovery Objectives

| Metric | Target |
|--------|--------|
| Recovery Time Objective (RTO) | < 4 hours |
| Recovery Point Objective (RPO) | < 1 hour |

### Backup and Restore
- Full database backup: Daily at 02:00 UTC
- Incremental backup: Every 6 hours
- Backup retention: 30 days
- Restore test frequency: Quarterly

Enterprise customers receive:
- Dedicated DR runbooks
- Annual DR drill participation option
- Custom RTO/RPO negotiation

---

## Compliance and Security Certifications

| Certification | Status | Renewal |
|--------------|--------|---------|
| SOC 2 Type II | Active | Annual |
| ISO 27001 | Active | Annual |
| GDPR | Compliant | Ongoing |
| CCPA | Compliant | Ongoing |
| HIPAA | Available (Enterprise + BAA) | Annual |
| PCI DSS Level 1 | Active | Annual |

Compliance documentation available at trust.example.com or by contacting legal@example.com.
