"""
create_data.py
Run this ONCE to create all mock data files and folders.
This simulates:
  - SharePoint documents (as local .txt files)
  - Knowledge Base source documents (for FAISS indexing)
  - Required folder structure

Usage:
    python create_data.py
"""

import os

def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ Created: {path}")


def create_all_data():
    print("\n" + "="*60)
    print("  Creating mock data files...")
    print("="*60)

    # ══════════════════════════════════════════════════════════
    #  LICENSING — SHAREPOINT DOCS
    # ══════════════════════════════════════════════════════════

    print("\n📁 Licensing > SharePoint")

    write_file("data/licensing/sharepoint/smart_account_guide.txt", """\
DOCUMENT: Licensing Smart Account Guide
SOURCE: SharePoint > Licensing > Smart Accounts
LAST UPDATED: 2024-01-15

WHAT IS A LICENSING SMART ACCOUNT?
A Licensing Smart Account is a centralized license management entity used to
organize, manage, and transfer software licenses across your organization.
It serves as the primary container for all Cisco software licenses purchased
under an enterprise agreement.

KEY FEATURES:
- Centralized license visibility across all virtual accounts
- Automated license assignment and rebalancing
- Compliance tracking and reporting dashboard
- Integration with Cisco Commerce Workspace (CCW)

SMART ACCOUNT HIERARCHY:
  Smart Account (Root)
    └── Virtual Account 1 (e.g., HQ Devices)
    └── Virtual Account 2 (e.g., Branch Offices)
    └── Virtual Account 3 (e.g., Data Center)

HOW TO CREATE A LICENSING SMART ACCOUNT:
1. Log in to software.cisco.com
2. Navigate to Smart Software Manager
3. Click "Request Smart Account"
4. Fill in organization details and domain identifier
5. Submit for approval (typically 24-48 hours)

SMART ACCOUNT ROLES:
- Smart Account Admin: Full access, can create/delete virtual accounts
- Virtual Account Admin: Manages licenses within a virtual account
- User: Read-only access to assigned virtual accounts

IMPORTANT NOTES:
- Each organization can have only ONE Smart Account
- Smart Account domain must match your company email domain
- Licenses remain active even when moved between virtual accounts
""")

    write_file("data/licensing/sharepoint/virtual_account_policy.txt", """\
DOCUMENT: Licensing Virtual Account Policy
SOURCE: SharePoint > Licensing > Virtual Accounts
LAST UPDATED: 2024-02-10

WHAT IS A LICENSING VIRTUAL ACCOUNT?
A Licensing Virtual Account is a sub-container within a Smart Account used to
organize licenses by business unit, geography, product line, or any logical
grouping that suits your organization's structure.

VIRTUAL ACCOUNT TYPES IN LICENSING:
1. DEFAULT Virtual Account  - Auto-created with Smart Account, cannot be deleted
2. CUSTOM Virtual Account   - Created by admins for specific groupings
3. REGIONAL Virtual Account - Organized by geographic region (e.g., APAC, EMEA)

LICENSE TRANSFER RULES:
- Licenses can be freely moved between virtual accounts within the same Smart Account
- Transfers are instant and do not interrupt active services
- Transfer history is logged for compliance auditing
- Cannot transfer licenses to a different Smart Account without re-purchase

COMPLIANCE AND REPORTING:
- Overage alerts trigger when usage exceeds allocated licenses in a virtual account
- Monthly compliance reports are auto-generated per virtual account
- Grace period: 90 days for license overages before enforcement

BEST PRACTICES:
- Keep virtual accounts aligned to cost centers for easy chargeback
- Review and rebalance licenses quarterly
- Set up alert thresholds at 80% utilization
- Name virtual accounts clearly: [Region]-[BU]-[Product]

CURRENT ACTIVE VIRTUAL ACCOUNTS (Sample):
- VA-001: HQ-Finance-DNA
- VA-002: APAC-Engineering-Catalyst
- VA-003: EMEA-Sales-Webex
- VA-004: US-DataCenter-UCS
""")

    # ══════════════════════════════════════════════════════════
    #  LICENSING — KB DOCS
    # ══════════════════════════════════════════════════════════

    print("\n📁 Licensing > KB")

    write_file("data/licensing/kb/licensing_faq.txt", """\
KNOWLEDGE BASE: Licensing Domain FAQ
CATEGORY: Licensing > General Questions

Q: What is the difference between a Licensing Smart Account and a regular account?
A: A Licensing Smart Account is a cloud-based license management system that
provides centralized visibility and control over all software licenses. Unlike
traditional PAK-based licensing, Smart Accounts allow instant license deployment,
easy transfers, and automated compliance tracking.

Q: How many virtual accounts can I create under a Licensing Smart Account?
A: There is no hard limit on the number of virtual accounts. However, best practice
recommends keeping it under 50 virtual accounts for manageable administration.
Most enterprise customers use 5-15 virtual accounts aligned to business units.

Q: What happens to licenses when a virtual account is deleted?
A: All licenses in a deleted virtual account are automatically moved to the DEFAULT
virtual account. No licenses are lost. You have 30 days to redistribute them
before they are permanently assigned to DEFAULT.

Q: Can I have multiple Smart Accounts for my organization?
A: Typically, one Smart Account per organization is recommended. However, large
enterprises with separate subsidiaries may have multiple Smart Accounts. Each
Smart Account requires a unique domain identifier.

Q: How do I handle license true-up for Licensing Smart Accounts?
A: True-up occurs annually. The system automatically calculates the delta between
contracted licenses and actual usage. Over-usage is billed at the true-up rate
specified in your enterprise agreement.

Q: What is the Licensing Smart Account activation process timeline?
A: Standard activation: 24-48 business hours.
   Express activation (for existing customers): 4-8 hours.
   Bulk activation for M&A scenarios: 5-7 business days.
""")

    write_file("data/licensing/kb/licensing_overview.txt", """\
KNOWLEDGE BASE: Licensing Domain Overview
CATEGORY: Licensing > Overview

LICENSING DOMAIN OVERVIEW
The Licensing domain manages all software license lifecycle activities including
procurement, assignment, compliance, and renewal for the enterprise.

KEY COMPONENTS:
1. Smart Software Manager (SSM)
   - Cloud portal for license management
   - URL: software.cisco.com
   - Supports Smart Licensing and Smart Licensing Using Policy (SLP)

2. Smart Licensing Using Policy (SLP)
   - Next-generation licensing model
   - No license reservation required
   - Usage reported via CSLU or direct cloud connection
   - Enforced after 90-day evaluation period

3. Cisco Smart License Utility (CSLU)
   - On-premises proxy for air-gapped environments
   - Synchronizes with SSM every 30 days
   - Supports offline synchronization via file exchange

LICENSE TYPES MANAGED:
- Perpetual licenses (one-time purchase, no expiry)
- Subscription licenses (annual or multi-year terms)
- Term licenses (fixed duration, e.g., 3-year DNA Advantage)
- Evaluation licenses (90-day trial, limited features)

COMPLIANCE STATUS DEFINITIONS:
- Authorized: License count meets or exceeds usage
- Out of Compliance: Usage exceeds license count (grace period active)
- Enforcement: Grace period expired, features may be restricted
- Evaluation Expired: Trial license has passed 90-day limit
""")

    # ══════════════════════════════════════════════════════════
    #  ONPREM — SHAREPOINT DOCS
    # ══════════════════════════════════════════════════════════

    print("\n📁 OnPrem > SharePoint")

    write_file("data/onprem/sharepoint/onprem_smart_account.txt", """\
DOCUMENT: OnPrem Smart Account Guide
SOURCE: SharePoint > OnPrem > Smart Accounts
LAST UPDATED: 2024-01-20

WHAT IS AN ONPREM SMART ACCOUNT?
An OnPrem Smart Account in the context of on-premises infrastructure refers to
a privileged local administrator account that has elevated access to on-premises
hardware, servers, network devices, and data center equipment.

This is DIFFERENT from a Licensing Smart Account — the OnPrem Smart Account is
a LOCAL SYSTEM account, not a cloud-based license management entity.

ONPREM SMART ACCOUNT TYPES:
1. LOCAL ADMIN ACCOUNT    - Full local system access on a single device
2. DOMAIN ADMIN ACCOUNT   - Full access across the Active Directory domain
3. SERVICE ACCOUNT        - Used by applications/services to run processes
4. BREAK-GLASS ACCOUNT    - Emergency access account, highly restricted

ONPREM SMART ACCOUNT SECURITY POLICIES:
- Passwords must be rotated every 30 days (auto-enforced via PAM tool)
- MFA required for all smart account logins
- All sessions recorded via CyberArk/Delinea session recording
- Dual approval required for break-glass account activation
- Accounts are disabled after 3 consecutive failed login attempts

ACCESS REQUEST PROCESS:
1. Submit access request in ServiceNow (RITM ticket)
2. Manager approval required within 24 hours
3. Security team reviews and provisions access
4. Access is time-bound (max 8 hours per session)
5. Session logs reviewed within 48 hours post-access

ONPREM SMART ACCOUNT INVENTORY (Sample):
- SVC-SQL-PROD     : SQL Server service account (Production)
- SVC-BACKUP-01    : Backup agent service account
- ADM-DATACENTER   : Data center admin account
- BRK-EMERGENCY    : Break-glass emergency account
""")

    write_file("data/onprem/sharepoint/onprem_setup_guide.txt", """\
DOCUMENT: OnPrem Infrastructure Setup Guide
SOURCE: SharePoint > OnPrem > Setup
LAST UPDATED: 2024-03-05

ONPREM INFRASTRUCTURE OVERVIEW
The OnPrem domain covers all physical and virtual infrastructure hosted within
the organization's own data centers, including servers, storage, networking,
and virtualization layers.

SUPPORTED ONPREM PLATFORMS:
- VMware vSphere / vCenter (virtualization)
- Microsoft Hyper-V (virtualization)
- Cisco UCS (bare metal servers)
- NetApp / Pure Storage (storage arrays)
- Cisco Nexus (data center networking)

ONPREM VIRTUAL ACCOUNT (Infrastructure Context):
In the OnPrem domain, Virtual Account refers to virtualized compute resources:
- VM Templates    : Pre-configured virtual machine images
- Resource Pools  : Logical grouping of CPU/RAM/Storage
- vApps           : Multi-tier application containers in vSphere

SETUP STEPS FOR NEW ONPREM ENVIRONMENT:
1. Rack and stack physical hardware
2. Configure BIOS/UEFI settings and RAID
3. Install hypervisor (vSphere ESXi or Hyper-V)
4. Connect to vCenter / SCVMM management plane
5. Configure networking (VLANs, vSwitches, NSX)
6. Set up storage (NFS, iSCSI, or FC)
7. Create resource pools and VM templates
8. Onboard to monitoring (SolarWinds / Dynatrace)
9. Register devices in CMDB (ServiceNow)

PATCHING POLICY:
- Critical patches: Applied within 72 hours of release
- Standard patches: Monthly patch cycle (3rd Sunday)
- Emergency patches: Immediate application with CAB approval
- Patch compliance target: 95% within 30 days

BACKUP POLICY:
- VMs: Daily snapshots, retained for 30 days
- Databases: Hourly log backups, daily full backups
- Physical servers: Weekly full image backup
- Offsite replication: Real-time to DR site
""")

    # ══════════════════════════════════════════════════════════
    #  ONPREM — KB DOCS
    # ══════════════════════════════════════════════════════════

    print("\n📁 OnPrem > KB")

    write_file("data/onprem/kb/onprem_faq.txt", """\
KNOWLEDGE BASE: OnPrem Domain FAQ
CATEGORY: OnPrem > General Questions

Q: What is the difference between an OnPrem Smart Account and a Licensing Smart Account?
A: They are completely different concepts. An OnPrem Smart Account is a privileged
local administrator account for accessing on-premises hardware and systems. A
Licensing Smart Account is a cloud-based portal for managing software licenses.
Do not confuse these two — they belong to separate domains.

Q: How do I request access to an OnPrem Smart Account?
A: Submit a RITM ticket in ServiceNow with justification. Your manager approves
within 24 hours, then the security team provisions time-bound access (max 8 hours).
All sessions are recorded via CyberArk.

Q: What is an OnPrem Virtual Account in the infrastructure context?
A: In OnPrem, a Virtual Account refers to virtualized compute resources such as
VMware resource pools, VM templates, or vApps. This is different from a
Licensing Virtual Account which is a license container.

Q: How many physical servers are currently in the OnPrem inventory?
A: Query the CMDB database for current counts. As of last audit: 240 physical
servers across 3 data centers (HQ, DR-East, DR-West).

Q: What monitoring tools are used for OnPrem infrastructure?
A: Primary: SolarWinds NPM for network, Dynatrace for application performance.
Secondary: vCenter performance dashboards, Cisco Intersight for UCS hardware.
Alerting: PagerDuty integration for Sev1/Sev2 alerts.

Q: What is the SLA for OnPrem server provisioning?
A: Standard VM provisioning: 4 business hours via self-service portal.
Physical server provisioning: 5-10 business days including procurement.
Template-based deployment: Under 30 minutes via automation pipeline.
""")

    write_file("data/onprem/kb/onprem_overview.txt", """\
KNOWLEDGE BASE: OnPrem Domain Overview
CATEGORY: OnPrem > Overview

ONPREM DOMAIN OVERVIEW
The OnPrem domain manages all on-premises infrastructure assets including
compute, storage, networking, and the associated accounts and access controls.

DATA CENTERS MANAGED:
- DC-HQ     : Primary data center, Headquarters (400 racks)
- DC-EAST   : DR site, East Coast (150 racks)
- DC-WEST   : DR site, West Coast (150 racks)

INFRASTRUCTURE TIERS:
- Tier 1 (Mission Critical): ERP, Core Banking, Patient Records
- Tier 2 (Business Critical): CRM, HR Systems, Analytics
- Tier 3 (Standard): Dev/Test, Internal Tools, Collaboration

CMDB INTEGRATION:
All OnPrem assets are registered in ServiceNow CMDB with:
- Asset tag and serial number
- Location (rack, row, data center)
- Owner (team and individual)
- Lifecycle status (Active, Decommissioned, In-Repair)
- Associated CIs (applications, databases, network devices)

CAPACITY MANAGEMENT:
- CPU utilization target: below 70% average
- Memory utilization target: below 75% average
- Storage utilization target: below 80% (alert at 75%)
- Network bandwidth target: below 60% average utilization

DISASTER RECOVERY:
- RTO (Recovery Time Objective): 4 hours for Tier 1
- RPO (Recovery Point Objective): 1 hour for Tier 1
- DR tests conducted: Quarterly (full failover test)
- Last DR test result: Passed (Jan 2024)
""")

    # ══════════════════════════════════════════════════════════
    #  KB DOMAIN — SHAREPOINT DOCS
    # ══════════════════════════════════════════════════════════

    print("\n📁 KB Domain > SharePoint")

    write_file("data/kb_domain/sharepoint/kb_management_guide.txt", """\
DOCUMENT: Knowledge Base Management Guide
SOURCE: SharePoint > KB Domain > Management
LAST UPDATED: 2024-02-28

KB DOMAIN OVERVIEW
The KB (Knowledge Base) domain manages the organization's internal knowledge
repository — articles, runbooks, SOPs, troubleshooting guides, and FAQs
used by IT, support teams, and end users.

KB PLATFORM: Confluence (self-hosted) + ServiceNow Knowledge Module

KB CATEGORIES:
1. IT Operations    - Runbooks, incident response, change procedures
2. HR & Policies    - Company policies, onboarding guides, benefits
3. Product Support  - Product manuals, release notes, known issues
4. Security         - Security advisories, compliance guides, audits
5. Finance          - Expense policies, procurement guides, approval flows

KB SMART ACCOUNT (KB Context):
In the KB domain, Smart Account refers to a Knowledge Author account with
elevated permissions to create, edit, approve, and publish articles.
Smart Account holders in KB are subject matter experts (SMEs) vetted by
the knowledge management team.

KB VIRTUAL ACCOUNT:
A KB Virtual Account is a reader/subscriber account with access to specific
knowledge spaces. Virtual accounts are provisioned for contractors,
partners, and temporary staff who need read-only access to curated spaces.

KB GOVERNANCE:
- All articles must be reviewed by an SME before publishing
- Articles expire after 12 months and must be re-certified
- Broken links auto-flagged within 24 hours
- Search quality scored monthly (click-through rate, deflection rate)

KB METRICS (Current):
- Total articles: 4,280
- Active authors (Smart Accounts): 142
- Monthly active readers (Virtual Accounts): 8,500
- Deflection rate: 68% (target: 75%)
- Average article rating: 4.2/5
""")

    # ══════════════════════════════════════════════════════════
    #  KB DOMAIN — KB DOCS
    # ══════════════════════════════════════════════════════════

    print("\n📁 KB Domain > KB")

    write_file("data/kb_domain/kb/kb_domain_overview.txt", """\
KNOWLEDGE BASE: KB Domain Overview
CATEGORY: KB Domain > Overview

KB DOMAIN OVERVIEW
The KB Domain team is responsible for building and maintaining the enterprise
knowledge repository that serves 8,500+ employees and partners globally.

KEY RESPONSIBILITIES:
- Content strategy and governance
- Author enablement and training
- Search optimization and analytics
- Platform administration (Confluence + ServiceNow KB)
- Integration with IT Service Desk for article deflection

KB AUTHOR ACCOUNT TYPES:
- Smart Account (KB): Full author rights — create, edit, publish, archive
- Virtual Account (KB): Reader account — search and view only
- Admin Account: Platform administration, user management, analytics

KNOWLEDGE LIFECYCLE:
  Draft → Review → Approved → Published → Certified → Archived

ONBOARDING NEW KB AUTHORS:
1. Submit KB access request via ServiceNow
2. Complete KB authoring training (2-hour e-learning)
3. Assigned a mentor (existing Smart Account holder)
4. First 3 articles reviewed and co-approved by mentor
5. Full Smart Account rights granted after probation period

SEARCH AND FINDABILITY:
- Elasticsearch-powered full-text search
- Tag taxonomy: 650+ controlled vocabulary tags
- Related articles auto-suggested via ML model
- Federated search integrated with MS Teams and Slack

SLA FOR KB REQUESTS:
- New article request: Published within 5 business days
- Article update request: Processed within 2 business days
- Broken link fix: Within 24 hours
- Emergency advisory: Within 2 hours (Sev1 incidents)
""")

    # ══════════════════════════════════════════════════════════
    #  CREATE EMPTY FOLDERS
    # ══════════════════════════════════════════════════════════

    os.makedirs("vector_stores", exist_ok=True)
    os.makedirs("db", exist_ok=True)
    print("\n📁 Created: vector_stores/")
    print("📁 Created: db/")

    # ══════════════════════════════════════════════════════════
    #  SUMMARY
    # ══════════════════════════════════════════════════════════

    print("\n" + "="*60)
    print("  ✅ All data files created successfully!")
    print("="*60)
    print("""
Next steps:
  1. python db/setup_db.py     ← create & seed the database
  2. python vector_store.py    ← build FAISS indexes
  3. python run.py             ← run the demo!
""")


if __name__ == "__main__":
    create_all_data()
