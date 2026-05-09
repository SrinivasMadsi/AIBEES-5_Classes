"""
setup_db.py
Creates and seeds the SQLite database with domain-specific tables.
Simulates the MySQL database used in production.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../db/enterprise.db")

def setup_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── LICENSING DOMAIN TABLES ───────────────────────────────────────────────

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS licensing_smart_accounts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        account_name    TEXT NOT NULL,
        domain          TEXT NOT NULL,
        status          TEXT NOT NULL,  -- Active, Suspended, Pending
        total_licenses  INTEGER DEFAULT 0,
        used_licenses   INTEGER DEFAULT 0,
        created_date    TEXT,
        admin_email     TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS licensing_virtual_accounts (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        smart_account_id      INTEGER,
        virtual_account_name  TEXT NOT NULL,
        region                TEXT,
        allocated_licenses    INTEGER DEFAULT 0,
        used_licenses         INTEGER DEFAULT 0,
        compliance_status     TEXT,  -- Authorized, Out of Compliance, Enforcement
        FOREIGN KEY (smart_account_id) REFERENCES licensing_smart_accounts(id)
    )""")

    # ── ONPREM DOMAIN TABLES ──────────────────────────────────────────────────

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS onprem_smart_accounts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        account_name    TEXT NOT NULL,
        account_type    TEXT NOT NULL,  -- LOCAL_ADMIN, DOMAIN_ADMIN, SERVICE, BREAK_GLASS
        status          TEXT NOT NULL,  -- Active, Disabled, Locked
        data_center     TEXT,
        last_login      TEXT,
        password_expiry TEXT,
        owner_team      TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS onprem_virtual_accounts (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        smart_account_id      INTEGER,
        virtual_account_name  TEXT NOT NULL,
        resource_type         TEXT,   -- VM_TEMPLATE, RESOURCE_POOL, VAPP
        cpu_allocated         INTEGER,
        ram_gb_allocated      INTEGER,
        storage_tb_allocated  REAL,
        status                TEXT,
        FOREIGN KEY (smart_account_id) REFERENCES onprem_smart_accounts(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS onprem_servers (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        hostname        TEXT NOT NULL,
        ip_address      TEXT,
        data_center     TEXT,
        tier            TEXT,  -- Tier1, Tier2, Tier3
        os              TEXT,
        status          TEXT,  -- Active, Decommissioned, In-Repair
        owner_team      TEXT,
        cpu_cores       INTEGER,
        ram_gb          INTEGER
    )""")

    # ── KB DOMAIN TABLES ──────────────────────────────────────────────────────

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kb_smart_accounts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        author_name     TEXT NOT NULL,
        email           TEXT NOT NULL,
        account_type    TEXT NOT NULL,  -- SMART (author), VIRTUAL (reader), ADMIN
        specialization  TEXT,
        articles_authored INTEGER DEFAULT 0,
        status          TEXT,  -- Active, Probation, Inactive
        joined_date     TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kb_articles (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        title           TEXT NOT NULL,
        category        TEXT,
        author_id       INTEGER,
        status          TEXT,  -- Draft, Published, Archived, Expired
        views           INTEGER DEFAULT 0,
        rating          REAL DEFAULT 0.0,
        created_date    TEXT,
        last_updated    TEXT,
        FOREIGN KEY (author_id) REFERENCES kb_smart_accounts(id)
    )""")

    # ── SEED DATA: LICENSING ──────────────────────────────────────────────────

    cursor.executemany("""
    INSERT OR IGNORE INTO licensing_smart_accounts
        (id, account_name, domain, status, total_licenses, used_licenses, created_date, admin_email)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", [
        (1, "Enterprise-SA-APAC",  "apac.company.com",   "Active",    5000, 4200, "2021-03-15", "sa-admin-apac@company.com"),
        (2, "Enterprise-SA-EMEA",  "emea.company.com",   "Active",    3000, 2750, "2021-06-01", "sa-admin-emea@company.com"),
        (3, "Enterprise-SA-AMER",  "amer.company.com",   "Active",    6000, 5100, "2020-11-20", "sa-admin-amer@company.com"),
        (4, "Enterprise-SA-INDIA", "india.company.com",  "Suspended",  800,  800, "2022-01-10", "sa-admin-india@company.com"),
    ])

    cursor.executemany("""
    INSERT OR IGNORE INTO licensing_virtual_accounts
        (id, smart_account_id, virtual_account_name, region, allocated_licenses, used_licenses, compliance_status)
    VALUES (?, ?, ?, ?, ?, ?, ?)""", [
        (1, 1, "VA-APAC-Finance",      "APAC",   800,  780, "Authorized"),
        (2, 1, "VA-APAC-Engineering",  "APAC",  1200, 1200, "Out of Compliance"),
        (3, 1, "VA-APAC-DataCenter",   "APAC",  1500, 1100, "Authorized"),
        (4, 2, "VA-EMEA-HQ",           "EMEA",  1000,  950, "Authorized"),
        (5, 2, "VA-EMEA-Branch",       "EMEA",  2000, 1800, "Authorized"),
        (6, 3, "VA-AMER-HQ",           "AMER",  2000, 1900, "Authorized"),
        (7, 3, "VA-AMER-Remote",       "AMER",  1500, 1200, "Authorized"),
        (8, 3, "VA-AMER-DataCenter",   "AMER",  2500, 2000, "Authorized"),
    ])

    # ── SEED DATA: ONPREM ─────────────────────────────────────────────────────

    cursor.executemany("""
    INSERT OR IGNORE INTO onprem_smart_accounts
        (id, account_name, account_type, status, data_center, last_login, password_expiry, owner_team)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", [
        (1, "SVC-SQL-PROD",     "SERVICE",      "Active",   "DC-HQ",    "2024-03-10", "2024-04-10", "DBA Team"),
        (2, "SVC-BACKUP-01",    "SERVICE",      "Active",   "DC-HQ",    "2024-03-11", "2024-04-11", "Infra Team"),
        (3, "ADM-DATACENTER",   "LOCAL_ADMIN",  "Active",   "DC-HQ",    "2024-03-09", "2024-03-25", "DC Ops"),
        (4, "BRK-EMERGENCY",    "BREAK_GLASS",  "Disabled", "DC-EAST",  "2024-01-05", "2024-04-05", "Security Ops"),
        (5, "ADM-NETWORK",      "DOMAIN_ADMIN", "Active",   "DC-WEST",  "2024-03-12", "2024-04-12", "Network Team"),
        (6, "SVC-MONITORING",   "SERVICE",      "Active",   "DC-HQ",    "2024-03-11", "2024-06-11", "Ops Team"),
    ])

    cursor.executemany("""
    INSERT OR IGNORE INTO onprem_virtual_accounts
        (id, smart_account_id, virtual_account_name, resource_type, cpu_allocated, ram_gb_allocated, storage_tb_allocated, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", [
        (1, 3, "RP-Production",    "RESOURCE_POOL", 256, 1024, 50.0, "Active"),
        (2, 3, "RP-Dev-Test",      "RESOURCE_POOL", 128,  512, 20.0, "Active"),
        (3, 3, "TMPL-Windows2022", "VM_TEMPLATE",     8,   32,  0.5, "Active"),
        (4, 3, "TMPL-RHEL9",       "VM_TEMPLATE",     4,   16,  0.3, "Active"),
        (5, 5, "VAPP-ERP-Stack",   "VAPP",           32,  256,  5.0, "Active"),
    ])

    cursor.executemany("""
    INSERT OR IGNORE INTO onprem_servers
        (id, hostname, ip_address, data_center, tier, os, status, owner_team, cpu_cores, ram_gb)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", [
        (1,  "PROD-SQL-01",   "10.0.1.10", "DC-HQ",    "Tier1", "Windows Server 2022", "Active",         "DBA Team",     32, 256),
        (2,  "PROD-APP-01",   "10.0.1.11", "DC-HQ",    "Tier1", "RHEL 9",              "Active",         "App Team",     16, 128),
        (3,  "PROD-APP-02",   "10.0.1.12", "DC-HQ",    "Tier1", "RHEL 9",              "Active",         "App Team",     16, 128),
        (4,  "DR-SQL-01",     "10.1.1.10", "DC-EAST",  "Tier1", "Windows Server 2022", "Active",         "DBA Team",     32, 256),
        (5,  "DEV-APP-01",    "10.0.2.10", "DC-HQ",    "Tier3", "Ubuntu 22.04",        "Active",         "Dev Team",      8,  32),
        (6,  "TEST-APP-01",   "10.0.2.11", "DC-HQ",    "Tier3", "Ubuntu 22.04",        "Active",         "QA Team",       8,  32),
        (7,  "LEGACY-SVR-01", "10.0.3.10", "DC-HQ",    "Tier2", "Windows Server 2016", "In-Repair",      "Infra Team",   16,  64),
        (8,  "PROD-WEB-01",   "10.0.1.20", "DC-HQ",    "Tier2", "RHEL 8",              "Active",         "Web Team",      8,  64),
        (9,  "PROD-WEB-02",   "10.0.1.21", "DC-HQ",    "Tier2", "RHEL 8",              "Active",         "Web Team",      8,  64),
        (10, "DECOM-SVR-01",  "10.0.9.10", "DC-WEST",  "Tier3", "Windows Server 2012", "Decommissioned", "Infra Team",    4,  16),
    ])

    # ── SEED DATA: KB DOMAIN ─────────────────────────────────────────────────

    cursor.executemany("""
    INSERT OR IGNORE INTO kb_smart_accounts
        (id, author_name, email, account_type, specialization, articles_authored, status, joined_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", [
        (1, "Priya Sharma",    "priya.s@company.com",   "SMART",   "IT Operations",    45, "Active",    "2021-02-01"),
        (2, "Rahul Mehta",     "rahul.m@company.com",   "SMART",   "Security",         32, "Active",    "2021-05-15"),
        (3, "Anita Patel",     "anita.p@company.com",   "SMART",   "HR & Policies",    28, "Active",    "2022-01-10"),
        (4, "James Wilson",    "james.w@company.com",   "SMART",   "Product Support",  19, "Probation", "2024-01-01"),
        (5, "Sara Chen",       "sara.c@company.com",    "ADMIN",   "Platform Admin",    5, "Active",    "2020-06-01"),
        (6, "Vendor User 01",  "vendor01@partner.com",  "VIRTUAL", "Read Only",         0, "Active",    "2024-02-01"),
        (7, "Contractor A",    "contractor@ext.com",    "VIRTUAL", "Read Only",         0, "Active",    "2024-03-01"),
    ])

    cursor.executemany("""
    INSERT OR IGNORE INTO kb_articles
        (id, title, category, author_id, status, views, rating, created_date, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", [
        (1,  "How to Reset VPN Credentials",               "IT Operations",  1, "Published", 3200, 4.5, "2022-03-01", "2024-01-15"),
        (2,  "Incident Response Runbook - Sev1",           "IT Operations",  1, "Published", 1800, 4.8, "2021-06-01", "2024-02-01"),
        (3,  "Phishing Email Identification Guide",        "Security",       2, "Published", 5400, 4.7, "2022-01-10", "2024-01-10"),
        (4,  "MFA Setup for Remote Access",                "Security",       2, "Published", 4200, 4.6, "2022-05-15", "2023-12-01"),
        (5,  "Employee Onboarding Checklist",              "HR & Policies",  3, "Published", 2900, 4.4, "2021-09-01", "2024-03-01"),
        (6,  "Expense Reimbursement Policy 2024",          "HR & Policies",  3, "Published", 1500, 4.2, "2024-01-01", "2024-01-01"),
        (7,  "Product Release Notes v4.2",                 "Product Support",4, "Published",  800, 3.9, "2024-02-01", "2024-02-15"),
        (8,  "Known Issues - Customer Portal Feb 2024",    "Product Support",4, "Draft",      200, 0.0, "2024-03-01", "2024-03-01"),
        (9,  "Data Classification Policy",                 "Security",       2, "Published", 2100, 4.5, "2022-08-01", "2023-11-01"),
        (10, "Server Patching SOP",                        "IT Operations",  1, "Published", 1600, 4.3, "2022-02-01", "2024-02-28"),
    ])

    conn.commit()
    conn.close()
    print("✅ Database created and seeded successfully at:", DB_PATH)


if __name__ == "__main__":
    setup_database()
