import type { FormConfig, Question } from "../types/api";

interface Props {
  config: FormConfig;
  values: Record<string, unknown>;
  onChange: (qid: string, value: unknown) => void;
}

export default function FormRenderer({ config, values, onChange }: Props) {
  return (
    <div className="space-y-8">
      {config.sections.map((section) => (
        <div key={section.section_id}>
          <h2 className="font-display text-xl font-semibold text-slate-900 border-b border-slate-200 pb-2 mb-4">
            {section.section_name}
          </h2>
          <div className="space-y-6">
            {section.sub_sections.map((sub) => (
              <div key={sub.sub_section_id} className="bg-white border border-slate-200 rounded-xl p-5">
                <h3 className="font-display font-semibold text-base text-slate-800 mb-4">
                  {sub.sub_section_name}
                </h3>
                <div className="space-y-4">
                  {sub.questions.map((q) => (
                    <QuestionField
                      key={q.question_id}
                      question={q}
                      value={values[String(q.question_id)]}
                      onChange={(v) => onChange(String(q.question_id), v)}
                      allValues={values}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function QuestionField({
  question,
  value,
  onChange,
  allValues,
}: {
  question: Question;
  value: unknown;
  onChange: (v: unknown) => void;
  allValues: Record<string, unknown>;
}) {
  // Determine if this question is required based on conditional logic
  const conditionalActive =
    question.required_if &&
    Object.entries(question.required_if).every(([condQid, condValue]) => {
      const actualValue = allValues[condQid];
      // The value might be a qid number or the actual string value
      return actualValue === condValue;
    });

  const isRequired = question.required === true || conditionalActive === true;

  if (question.required_if && !conditionalActive) {
    // Show but mark as not required
  }

  const labelStyle = "block text-sm font-medium text-slate-700 mb-1";
  const inputStyle =
    "w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none";

  return (
    <div>
      <label className={labelStyle}>
        <span className="font-mono text-xs text-slate-400 mr-2">Q{question.question_id}</span>
        {question.question_text}
        {isRequired && <span className="text-red-500 ml-1">*</span>}
      </label>

      {question.response_type === "radio" && question.values && (
        <div className="flex gap-4 mt-1">
          {question.values.map((opt) => (
            <label key={opt.qid} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name={`q_${question.question_id}`}
                value={opt.qid}
                checked={value === opt.qid || value === opt.value}
                onChange={() => onChange(opt.qid)}
                className="text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-slate-700">{opt.value}</span>
            </label>
          ))}
        </div>
      )}

      {question.response_type === "select" && question.values && (
        <select
          className={inputStyle}
          value={String(value ?? "")}
          onChange={(e) => {
            const val = e.target.value;
            const opt = question.values?.find((o) => String(o.qid) === val);
            onChange(opt ? opt.qid : val);
          }}
        >
          <option value="">-- Select --</option>
          {question.values.map((opt) => (
            <option key={opt.qid} value={opt.qid}>
              {opt.value}
            </option>
          ))}
        </select>
      )}

      {question.response_type === "date" && (
        <input
          type="date"
          className={inputStyle}
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value)}
        />
      )}

      {(question.response_type === "currency" || question.response_type === "number") && (
        <input
          type="number"
          className={inputStyle}
          value={value === null || value === undefined ? "" : String(value)}
          onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
          placeholder={question.response_type === "currency" ? "USD" : "0"}
        />
      )}

      {question.response_type === "text" && (
        <input
          type="text"
          className={inputStyle}
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </div>
  );
}
