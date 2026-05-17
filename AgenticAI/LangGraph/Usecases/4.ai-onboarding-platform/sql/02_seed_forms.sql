-- =============================================================================
-- AI_Onboarding_Platform — Seed Form Configurations
-- =============================================================================
-- Loads the two forms: Benefits & Services + Clinical
-- Run AFTER 01_create_tables.sql
-- =============================================================================

SET search_path TO business_data, public;

-- ---------------------------------------------------------------------------
-- FORM 1: Benefits & Services
-- ---------------------------------------------------------------------------
INSERT INTO business_data.forms (form_id, form_name, version, config) VALUES
(1005, 'Benefits & Services', 'v1.0', $JSON${
  "form_id": 1005,
  "form_name": "Benefits & Services",
  "version": "v1.0",
  "sections": [
    {
      "section_id": 10050,
      "section_name": "Accumulator",
      "sub_sections": [
        {
          "sub_section_id": 1110050,
          "sub_section_name": "General Accumulator",
          "questions": [
            {
              "question_id": 121,
              "question_text": "Does the plan have accumulators?",
              "response_type": "radio",
              "values": [
                {"qid": 12, "value": "Yes"},
                {"qid": 13, "value": "No"}
              ],
              "required": true
            },
            {
              "question_id": 122,
              "question_text": "What is the contract year start date?",
              "response_type": "date",
              "required_if": {"121": "Yes"}
            },
            {
              "question_id": 123,
              "question_text": "Accumulator type",
              "response_type": "select",
              "values": [
                {"qid": 14, "value": "family-only"},
                {"qid": 15, "value": "combined"},
                {"qid": 16, "value": "individual-only"}
              ],
              "required_if": {"121": "Yes"}
            }
          ]
        },
        {
          "sub_section_id": 1110052,
          "sub_section_name": "Out of Pocket",
          "questions": [
            {
              "question_id": 141,
              "question_text": "Individual OOP maximum (USD)",
              "response_type": "currency",
              "required": true
            },
            {
              "question_id": 142,
              "question_text": "Family OOP maximum (USD)",
              "response_type": "currency",
              "required": true
            },
            {
              "question_id": 143,
              "question_text": "Does OOP include prescription drugs?",
              "response_type": "radio",
              "values": [
                {"qid": 17, "value": "Yes"},
                {"qid": 18, "value": "No"}
              ],
              "required": true
            }
          ]
        },
        {
          "sub_section_id": 1110053,
          "sub_section_name": "Deductible",
          "questions": [
            {
              "question_id": 151,
              "question_text": "Individual deductible (USD)",
              "response_type": "currency",
              "required": true
            },
            {
              "question_id": 152,
              "question_text": "Family deductible (USD)",
              "response_type": "currency",
              "required": true
            },
            {
              "question_id": 153,
              "question_text": "Does deductible reset on plan year boundary?",
              "response_type": "radio",
              "values": [
                {"qid": 19, "value": "Yes"},
                {"qid": 20, "value": "No"}
              ],
              "required": true
            }
          ]
        },
        {
          "sub_section_id": 1110054,
          "sub_section_name": "Co-pay",
          "questions": [
            {
              "question_id": 161,
              "question_text": "Office visit co-pay (USD)",
              "response_type": "currency",
              "required": true
            },
            {
              "question_id": 162,
              "question_text": "Specialist co-pay (USD)",
              "response_type": "currency",
              "required": true
            },
            {
              "question_id": 163,
              "question_text": "Emergency room co-pay (USD)",
              "response_type": "currency",
              "required": true
            }
          ]
        }
      ]
    }
  ]
}$JSON$::jsonb);

-- ---------------------------------------------------------------------------
-- FORM 2: Clinical
-- ---------------------------------------------------------------------------
INSERT INTO business_data.forms (form_id, form_name, version, config) VALUES
(2005, 'Clinical', 'v1.0', $JSON${
  "form_id": 2005,
  "form_name": "Clinical",
  "version": "v1.0",
  "sections": [
    {
      "section_id": 20050,
      "section_name": "Clinical Programs",
      "sub_sections": [
        {
          "sub_section_id": 1110080,
          "sub_section_name": "Prior Authorization",
          "questions": [
            {
              "question_id": 171,
              "question_text": "Is prior authorization required for specialty drugs?",
              "response_type": "radio",
              "values": [
                {"qid": 21, "value": "Yes"},
                {"qid": 22, "value": "No"}
              ],
              "required": true
            },
            {
              "question_id": 172,
              "question_text": "Maximum turnaround time (days)",
              "response_type": "number",
              "required_if": {"171": "Yes"}
            },
            {
              "question_id": 173,
              "question_text": "Urgent request turnaround (hours)",
              "response_type": "number",
              "required_if": {"171": "Yes"}
            }
          ]
        },
        {
          "sub_section_id": 1110081,
          "sub_section_name": "Utilization Management",
          "questions": [
            {
              "question_id": 181,
              "question_text": "Is UM review required for inpatient admissions?",
              "response_type": "radio",
              "values": [
                {"qid": 23, "value": "Yes"},
                {"qid": 24, "value": "No"}
              ],
              "required": true
            },
            {
              "question_id": 182,
              "question_text": "Criteria reference URL",
              "response_type": "text",
              "required_if": {"181": "Yes"}
            },
            {
              "question_id": 183,
              "question_text": "Concurrent review frequency (days)",
              "response_type": "number",
              "required_if": {"181": "Yes"}
            }
          ]
        },
        {
          "sub_section_id": 1110082,
          "sub_section_name": "Care Management",
          "questions": [
            {
              "question_id": 191,
              "question_text": "Is care management offered?",
              "response_type": "radio",
              "values": [
                {"qid": 25, "value": "Yes"},
                {"qid": 26, "value": "No"}
              ],
              "required": true
            },
            {
              "question_id": 192,
              "question_text": "Enrollment criteria diagnoses (comma-separated ICD codes)",
              "response_type": "text",
              "required_if": {"191": "Yes"}
            },
            {
              "question_id": 193,
              "question_text": "Care manager contact frequency",
              "response_type": "select",
              "values": [
                {"qid": 27, "value": "weekly"},
                {"qid": 28, "value": "biweekly"},
                {"qid": 29, "value": "monthly"},
                {"qid": 30, "value": "quarterly"}
              ],
              "required_if": {"191": "Yes"}
            }
          ]
        },
        {
          "sub_section_id": 1110083,
          "sub_section_name": "Eligibility",
          "questions": [
            {
              "question_id": 201,
              "question_text": "Eligibility verification method",
              "response_type": "select",
              "values": [
                {"qid": 31, "value": "real-time"},
                {"qid": 32, "value": "batch"},
                {"qid": 33, "value": "manual"}
              ],
              "required": true
            },
            {
              "question_id": 202,
              "question_text": "Eligibility refresh frequency (hours)",
              "response_type": "number",
              "required": true
            },
            {
              "question_id": 203,
              "question_text": "Allow retroactive eligibility?",
              "response_type": "radio",
              "values": [
                {"qid": 34, "value": "Yes"},
                {"qid": 35, "value": "No"}
              ],
              "required": true
            }
          ]
        }
      ]
    }
  ]
}$JSON$::jsonb);

-- ---------------------------------------------------------------------------
-- Seed sample clients (for IPM to select when filling forms)
-- ---------------------------------------------------------------------------
INSERT INTO business_data.clients (client_id, name, industry, plan_year_start, is_high_risk) VALUES
('CLIENT-ACME-001',        'ACME Healthcare',           'Healthcare',      '2026-01-01', false),
('CLIENT-INNOVA-002',      'Innova Tech Solutions',     'Technology',      '2026-07-01', false),
('CLIENT-GLOBALCORP-003',  'GlobalCorp Industries',     'Manufacturing',   '2026-01-01', true),
('CLIENT-MEDIRX-004',      'MediRx Pharmaceuticals',    'Pharmaceuticals', '2026-01-01', false),
('CLIENT-SUNRISE-005',     'Sunrise Financial Group',   'Finance',         '2026-07-01', false);

-- ---------------------------------------------------------------------------
-- Verify
-- ---------------------------------------------------------------------------
SELECT
  (SELECT count(*) FROM business_data.forms)   AS forms_loaded,
  (SELECT count(*) FROM business_data.clients) AS clients_loaded;
