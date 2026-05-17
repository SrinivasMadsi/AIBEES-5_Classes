-- =============================================================================
-- AI_Onboarding_Platform — Database Schema
-- =============================================================================
-- Creates the business_data schema and all tables.
-- Run this once in Neon SQL Editor BEFORE running 02_seed_forms.sql.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS business_data;

SET search_path TO business_data, public;

-- =============================================================================
-- forms: stores form configurations (Benefits & Services, Clinical, etc.)
-- =============================================================================
DROP TABLE IF EXISTS business_data.forms CASCADE;
CREATE TABLE business_data.forms (
    id              SERIAL PRIMARY KEY,
    form_id         INTEGER UNIQUE NOT NULL,             -- e.g., 1005
    form_name       VARCHAR(200) NOT NULL,
    version         VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    config          JSONB NOT NULL,                       -- full sections/subsections/questions
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_forms_form_id ON business_data.forms(form_id);

-- =============================================================================
-- clients: enterprise clients being onboarded
-- =============================================================================
DROP TABLE IF EXISTS business_data.clients CASCADE;
CREATE TABLE business_data.clients (
    id                SERIAL PRIMARY KEY,
    client_id         VARCHAR(50) UNIQUE NOT NULL,        -- e.g., "CLIENT-ACME-001"
    name              VARCHAR(200) NOT NULL,
    industry          VARCHAR(100),
    plan_year_start   DATE,
    is_high_risk      BOOLEAN DEFAULT false,
    created_at        TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_clients_client_id ON business_data.clients(client_id);

-- =============================================================================
-- submissions: IPM submissions (the form data)
-- =============================================================================
DROP TABLE IF EXISTS business_data.submissions CASCADE;
CREATE TABLE business_data.submissions (
    id               SERIAL PRIMARY KEY,
    submission_id    VARCHAR(50) UNIQUE NOT NULL,         -- e.g., "sub_2026_001234"
    client_id        VARCHAR(50) NOT NULL,
    client_name      VARCHAR(200) NOT NULL,
    form_id          INTEGER NOT NULL,
    form_version     VARCHAR(20) NOT NULL,
    submitted_by     VARCHAR(200) NOT NULL,                -- IPM email
    answers          JSONB NOT NULL,                       -- the raw submission
    status           VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, submitted, validating, validated_pass, validated_with_fixes, pending_human_review, approved, rejected
    plan_type        VARCHAR(20),                          -- HMO, PPO, HDHP, EPO (after intake classification)
    thread_id        VARCHAR(100),                         -- LangGraph thread for resume
    iteration_count  INTEGER DEFAULT 0,
    created_at       TIMESTAMPTZ DEFAULT now(),
    updated_at       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_submissions_status ON business_data.submissions(status);
CREATE INDEX idx_submissions_client ON business_data.submissions(client_id);

-- =============================================================================
-- findings: validation findings produced by the Validation Agent
-- =============================================================================
DROP TABLE IF EXISTS business_data.findings CASCADE;
CREATE TABLE business_data.findings (
    id                SERIAL PRIMARY KEY,
    submission_id     VARCHAR(50) NOT NULL,
    rule_id           VARCHAR(50) NOT NULL,
    rule_name         VARCHAR(200) NOT NULL,
    domain            VARCHAR(50) NOT NULL,                 -- accumulator, financial, clinical
    affected_field    VARCHAR(100) NOT NULL,
    status            VARCHAR(20) NOT NULL,                 -- pass, warning, fail
    severity          VARCHAR(30) NOT NULL,                 -- info, warning, fail_fixable, fail_reject
    current_value     JSONB,
    expected_value    JSONB,
    message           TEXT,
    suggested_fix     JSONB,                                -- {action, field, new_value, reason}
    auto_applied      BOOLEAN DEFAULT false,
    created_at        TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_findings_submission ON business_data.findings(submission_id);
CREATE INDEX idx_findings_status ON business_data.findings(status);

-- =============================================================================
-- human_reviews: HITL queue for BOM analyst review
-- =============================================================================
DROP TABLE IF EXISTS business_data.human_reviews CASCADE;
CREATE TABLE business_data.human_reviews (
    id                  SERIAL PRIMARY KEY,
    submission_id       VARCHAR(50) NOT NULL,
    finding_id          INTEGER,
    rule_id             VARCHAR(50),
    affected_field      VARCHAR(100),
    issue_description   TEXT NOT NULL,
    agent_recommendation TEXT,
    status              VARCHAR(30) NOT NULL DEFAULT 'pending', -- pending, approved, rejected, overridden
    assigned_to         VARCHAR(200) DEFAULT 'bom_analyst_queue',
    reviewed_by         VARCHAR(200),
    decision_comment    TEXT,
    decided_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_reviews_status ON business_data.human_reviews(status);
CREATE INDEX idx_reviews_submission ON business_data.human_reviews(submission_id);

-- =============================================================================
-- audit_log: compliance trail for every important event
-- =============================================================================
DROP TABLE IF EXISTS business_data.audit_log CASCADE;
CREATE TABLE business_data.audit_log (
    id              SERIAL PRIMARY KEY,
    submission_id   VARCHAR(50),
    event_type      VARCHAR(50) NOT NULL,                  -- form_submitted, validation_started, rule_failed, human_decision, etc.
    actor           VARCHAR(200),                          -- IPM email or BOM analyst email
    event_data      JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_audit_submission ON business_data.audit_log(submission_id);
CREATE INDEX idx_audit_event_type ON business_data.audit_log(event_type);

-- =============================================================================
-- Verify
-- =============================================================================
SELECT 'business_data tables created' AS status,
       count(*) AS table_count
FROM information_schema.tables
WHERE table_schema = 'business_data';
