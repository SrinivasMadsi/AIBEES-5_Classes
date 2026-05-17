// Types matching backend models

export interface QuestionOption {
  qid: number;
  value: string;
}

export interface Question {
  question_id: number;
  question_text: string;
  response_type: "radio" | "select" | "date" | "currency" | "number" | "text";
  values?: QuestionOption[];
  required?: boolean;
  required_if?: Record<string, string>;
}

export interface SubSection {
  sub_section_id: number;
  sub_section_name: string;
  questions: Question[];
}

export interface Section {
  section_id: number;
  section_name: string;
  sub_sections: SubSection[];
}

export interface FormConfig {
  form_id: number;
  form_name: string;
  version: string;
  sections: Section[];
}

export interface FormSummary {
  form_id: number;
  form_name: string;
  version: string;
}

export interface Client {
  client_id: string;
  name: string;
  industry: string | null;
  plan_year_start: string | null;
  is_high_risk: boolean;
}

export interface Finding {
  rule_id: string;
  rule_name: string;
  domain: string;
  affected_field: string;
  status: "pass" | "warning" | "fail";
  severity: "info" | "warning" | "fail_fixable" | "fail_reject";
  current_value: unknown;
  expected_value: unknown;
  message: string;
  suggested_fix: unknown;
  auto_applied: boolean;
}

export interface Submission {
  submission_id: string;
  client_id: string;
  client_name: string;
  form_id: number;
  form_version: string;
  submitted_by: string;
  answers?: Record<string, unknown>;
  status: string;
  plan_type: string | null;
  thread_id?: string;
  iteration_count: number;
  created_at: string | null;
  updated_at: string | null;
  findings?: Finding[];
}

export interface ValidationResult {
  submission_id: string;
  verdict: string;
  final_status: string;
  summary: string;
  plan_type: string;
  iteration_count: number;
  findings_count: number;
  human_review_items: unknown[];
}

export interface Review {
  review_id: number;
  submission_id: string;
  client_name: string;
  form_id: number;
  submitted_by: string;
  rule_id: string;
  affected_field: string;
  issue_description: string;
  agent_recommendation: string;
  status: string;
  created_at: string | null;
}

export interface ReviewDetail extends Review {
  plan_type: string | null;
  answers: Record<string, unknown> | null;
  finding: Finding | null;
}
