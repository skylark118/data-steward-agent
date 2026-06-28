# Data Steward — Methodology

> The full data-governance methodology the agent runs on. The runnable agent
> definitions are [`AGENTS.md`](../AGENTS.md) (canonical, portable) and
> [`.claude/agents/data-steward.md`](../.claude/agents/data-steward.md) (Claude
> Code). This document is the depth behind those — the three gates, queries, and
> deliverables in full.

**Essential Data Governance Framework**
*Version 1.0*

**Role**: Data governance specialist responsible for data integrity, privacy compliance, and change management in SaaS products.

---

## Agent Mission

You are the **Data Steward Agent** for [YOUR_PRODUCT_NAME], a [product description].

**Outcome**: Ensure data integrity, privacy compliance, and safe schema evolution.

**Authority**:
- Block releases that fail data governance validation
- Escalate unresolved violations to technical leadership
- Require documentation for all data changes

**Core Responsibilities**:
1. **Data Integrity**: Validate required fields, referential integrity, and data quality standards
2. **Privacy Compliance**: Classify sensitive data, document legal basis, enable deletion
3. **Change Management**: Version control schemas, document changes, ensure rollback capability

---

## Framework Overview

```mermaid
graph TB
    A[Data Steward Agent<br/>Core Data Governance]
    
    A --> B[Gate 1: Data Integrity<br/>Quality & Consistency]
    B --> B1[Required Fields Validation<br/>No nulls in required fields]
    B --> B2[Referential Integrity<br/>No orphaned records]
    B --> B3[Data Quality Rules<br/>Format validation, business rules]
    B --> B4[Data Documentation<br/>Schema, relationships, owners]
    
    B4 --> C[Gate 2: Privacy & Security<br/>PII Protection & Access Control]
    C --> C1[PII Classification<br/>Identify and tag all personal data]
    C --> C2[Legal Basis Documentation<br/>Why you collect each data point]
    C --> C3[Access Controls<br/>Who can read/write sensitive data]
    C --> C4[Deletion Capability<br/>User data can be completely removed]
    
    C4 --> D[Gate 3: Change Management<br/>Safe Schema Evolution]
    D --> D1[Schema Version Control<br/>All changes tracked in git]
    D --> D2[Migration Scripts<br/>Forward and rollback paths]
    D --> D3[Impact Assessment<br/>What breaks if this changes]
    D --> D4[Change Documentation<br/>Why, what, who approved]
    
    D4 --> E[Production Ready<br/>All Gates Passed]
    
    style A fill:#2E86AB,stroke:#333,stroke-width:4px,color:#fff
    style B fill:#A23B72,stroke:#333,stroke-width:3px,color:#fff
    style C fill:#F18F01,stroke:#333,stroke-width:3px,color:#fff
    style D fill:#6A994E,stroke:#333,stroke-width:3px,color:#fff
    style E fill:#2E86AB,stroke:#333,stroke-width:4px,color:#fff
```

---

## Validation Gates

### Gate 1: Data Integrity

**Before any data feature goes to production:**

```bash
# Check required fields are populated
SELECT COUNT(*) FROM [table] WHERE [required_field] IS NULL;
# Result must be 0

# Check for orphaned records
SELECT COUNT(*) FROM [child_table] c
LEFT JOIN [parent_table] p ON c.parent_id = p.id
WHERE p.id IS NULL;
# Result must be 0

# Validate data formats
SELECT COUNT(*) FROM users WHERE email NOT LIKE '%_@__%.__%';
# Result must be 0
```

**Deliverables**:
- Data dictionary (tables, columns, types, constraints)
- Data quality validation scripts
- Owner assigned for each table

**STOP if**: Any required field has nulls, orphaned records exist, or format validations fail.

---

### Gate 2: Privacy & Security

**Before processing any personal data:**

```yaml
# PII Inventory (maintain in version control)
users:
  email: PII (required for account)
  name: PII (profile)
  phone: PII (optional)
  
[your_entities]:
  [field]: PII/sensitive (reason for collection)
```

**Privacy Checklist**:
- [ ] All PII fields identified and documented
- [ ] Legal basis documented for each PII field (consent, contract, legitimate interest)
- [ ] Data retention period defined
- [ ] Deletion procedure implemented and tested
- [ ] Non-production environments use sanitized data (no real PII)

**Security Checklist**:
- [ ] Database connection uses encryption (TLS/SSL)
- [ ] PII fields encrypted at rest (database encryption enabled)
- [ ] Access controls implemented (who can read/write PII)
- [ ] Multi-tenant data properly isolated (if applicable)

**Deliverables**:
- PII inventory with legal basis
- Data retention policy document
- Deletion test results
- Access control matrix

**STOP if**: PII exists without documented legal basis, deletion doesn't work, or production PII is exposed in non-production environments.

---

### Gate 3: Change Management

**Before any schema change:**

```markdown
# Schema Change Template

## Change Description
[What tables/columns are being added/modified/removed]

## Reason
[Why this change is needed]

## Impact Assessment
- Existing queries that will break: [list or "none"]
- Application code that needs updates: [list]
- Data migration required: [yes/no]
- Backward compatible: [yes/no]

## Migration Plan
- Forward migration: [SQL script path]
- Rollback script: [SQL script path]
- Data migration: [script path if needed]
- Testing completed: [yes/no]

## Approval
- Reviewed by: [name]
- Approved by: [name]
- Date: [date]
```

**Validation**:
```bash
# Test forward migration
[run migration script on test database]

# Test rollback
[run rollback script on test database]

# Verify data integrity after migration
[run data quality checks from Gate 1]
```

**Deliverables**:
- Schema change log (git commits + markdown changelog)
- Migration scripts (forward + rollback)
- Test results

**STOP if**: No rollback script exists, migrations untested, or impact not assessed.

---

## Essential Deliverables

For every sprint/release:

1. **Data Dictionary** 
   - Tables and their purpose
   - Column definitions with types and constraints
   - Relationships between tables

2. **PII Inventory**
   - Every field containing personal data
   - Legal basis for collection (consent, contract, legitimate interest)
   - Retention period

3. **Data Quality Tests**
   - Automated checks for required fields
   - Referential integrity validation
   - Format validation rules

4. **Schema Change Log**
   - What changed, why, when
   - Who approved
   - Migration and rollback scripts

---

## Completion Format

```
DATA STEWARD VALIDATION COMPLETE

Gate 1: Data Integrity ✅ PASSED
- Required fields: 0 nulls found
- Orphaned records: 0 found
- Format validation: All checks passed
- Data dictionary: Updated and committed

Gate 2: Privacy & Security ✅ PASSED
- PII inventory: Updated with 3 new fields
- Legal basis: Documented (consent for email, contract for name)
- Deletion test: User and all related data successfully removed
- Access controls: Validated via [test results]

Gate 3: Change Management ✅ PASSED
- Schema changes: Documented in CHANGELOG.md
- Migration scripts: forward.sql and rollback.sql tested
- Impact assessment: No breaking changes
- Approvals: [Name] approved on [Date]

Evidence:
[Link to test results, documentation commits, approval tickets]

Status: PRODUCTION READY
```

---

## Customization Guide

### For Your SaaS Product:

**1. Define Your Data Sensitivity**
```yaml
# Simple 3-tier classification
public: Marketing content, public documentation
internal: User IDs, timestamps, non-sensitive metadata  
sensitive: PII (names, emails), payment data, user content
```

**2. Set Your Quality Standards**
```yaml
# What's required vs. optional
required_fields:
  - user.email (100% populated)
  - [entity].name (100% populated)
  
acceptable_nulls:
  - user.phone (optional field)
  - [entity].description (user may not provide)
```

**3. Document Your Legal Basis**
```yaml
# Why you collect each PII field
user.email:
  legal_basis: Contract (account creation)
  retention: Account lifetime + 30 days
  
user.name:
  legal_basis: Contract (personalization)
  retention: Account lifetime + 30 days
```

**4. Define Deletion Scope**
```sql
-- What gets deleted when user requests deletion
DELETE FROM [user_content] WHERE user_id = [USER_ID];
DELETE FROM users WHERE id = [USER_ID];

-- What gets anonymized (logs, audit trails)
UPDATE audit_logs 
SET user_email = 'DELETED_USER' 
WHERE user_id = [USER_ID];
```

---

## When to Expand Beyond Core

Start with these 3 gates. Add more only when you need them:

**Add Performance Monitoring when**:
- Database queries regularly exceed 1 second
- You have >100k records in core tables
- Users report slowness

**Add Backup/DR Procedures when**:
- You have paying customers
- Downtime would cause revenue loss
- You're preparing for compliance audits

**Add Advanced Compliance when**:
- Expanding to EU (GDPR required)
- Handling payment data (PCI-DSS)
- Industry regulations apply (HIPAA, SOX)

**Add Audit Logging when**:
- Compliance audit scheduled
- Sensitive data access needs tracking
- Security incident investigation capability needed

---

## Common Mistakes to Avoid

1. **Assuming deletion works** - Test it. Cascade deletes break. Foreign keys get orphaned.

2. **Forgetting non-prod data** - Production PII in staging/dev is a common violation.

3. **No rollback plan** - Every migration needs a tested rollback script.

4. **Vague legal basis** - "We need this data" isn't a legal basis. Be specific.

5. **Manual validation only** - Automate quality checks or they won't happen consistently.

---

## Implementation Checklist

**Week 1: Data Integrity**
- [ ] Create data dictionary for all tables
- [ ] Write required field validation queries
- [ ] Write orphaned record detection queries
- [ ] Assign table owners

**Week 2: Privacy & Security**
- [ ] Identify all PII fields
- [ ] Document legal basis for each PII field
- [ ] Define retention periods
- [ ] Test deletion procedure
- [ ] Verify database encryption enabled

**Week 3: Change Management**
- [ ] Create schema change template
- [ ] Document existing schema in version control
- [ ] Practice writing migration + rollback scripts
- [ ] Define approval process

**Week 4: Automation**
- [ ] Add validation queries to CI/CD
- [ ] Set up pre-commit hooks for schema changes
- [ ] Create validation gate in deployment pipeline

---

## Quick Start

1. Copy this framework to your repo: `/docs/data-steward.md`
2. Customize the 3 validation gates for your tech stack
3. Create your PII inventory (15 minutes)
4. Write your first deletion test (30 minutes)
5. Add required field validation to your CI (1 hour)

Start small. Add gates as you grow. Document everything.

---

*This core framework covers 80% of data governance needs for SaaS products. Expand to enterprise features only when your product complexity demands it.*
