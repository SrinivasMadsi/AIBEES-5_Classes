import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Save, Send } from "lucide-react";
import PageHeader from "../components/PageHeader";
import FormRenderer from "../components/FormRenderer";
import { createSubmission, getForm, listClients, validateSubmission } from "../lib/api";
import type { Client, FormConfig } from "../types/api";

export default function FormFillPage() {
  const { formId } = useParams<{ formId: string }>();
  const navigate = useNavigate();

  const [config, setConfig] = useState<FormConfig | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<string>("");
  const [submittedBy, setSubmittedBy] = useState("ipm@healthcare.com");
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [submitting, setSubmitting] = useState(false);
  const [validating, setValidating] = useState(false);
  const [submissionId, setSubmissionId] = useState<string | null>(null);

  useEffect(() => {
    if (formId) {
      getForm(Number(formId))
        .then((r) => setConfig(r.config))
        .catch(console.error);
    }
    listClients().then(setClients).catch(console.error);
  }, [formId]);

  const handleSaveSubmit = async () => {
    if (!config || !selectedClient) {
      alert("Please select a client first");
      return;
    }
    const client = clients.find((c) => c.client_id === selectedClient);
    if (!client) return;

    setSubmitting(true);
    try {
      const res = await createSubmission({
        client_id: client.client_id,
        client_name: client.name,
        form_id: config.form_id,
        form_version: config.version,
        submitted_by: submittedBy,
        answers: values,
      });
      setSubmissionId(res.submission_id);
    } catch (err) {
      console.error(err);
      alert("Failed to submit form");
    } finally {
      setSubmitting(false);
    }
  };

  const handleValidate = async () => {
    if (!submissionId) return;
    setValidating(true);
    try {
      await validateSubmission(submissionId);
      navigate(`/submissions/${submissionId}`);
    } catch (err) {
      console.error(err);
      alert("Validation failed");
    } finally {
      setValidating(false);
    }
  };

  return (
    <div>
      <PageHeader
        title={config?.form_name ?? "Loading..."}
        subtitle={`Form ID ${formId} · IPM submission`}
        right={
          <div className="flex gap-2">
            {!submissionId && (
              <button
                onClick={handleSaveSubmit}
                disabled={submitting || !selectedClient}
                className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white px-4 py-2 rounded-lg text-sm font-medium"
              >
                <Save className="w-4 h-4" />
                {submitting ? "Saving..." : "Save Submission"}
              </button>
            )}
            {submissionId && (
              <button
                onClick={handleValidate}
                disabled={validating}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white px-4 py-2 rounded-lg text-sm font-medium"
              >
                <Send className="w-4 h-4" />
                {validating ? "Validating..." : "Validate Now"}
              </button>
            )}
          </div>
        }
      />

      <div className="p-8 max-w-4xl">
        {/* Client + Submitter */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 mb-6">
          <h3 className="font-display font-semibold text-base text-slate-800 mb-4">
            Submission Context
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Client</label>
              <select
                className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
                value={selectedClient}
                onChange={(e) => setSelectedClient(e.target.value)}
                disabled={!!submissionId}
              >
                <option value="">-- Select client --</option>
                {clients.map((c) => (
                  <option key={c.client_id} value={c.client_id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Submitted by</label>
              <input
                type="email"
                className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
                value={submittedBy}
                onChange={(e) => setSubmittedBy(e.target.value)}
                disabled={!!submissionId}
              />
            </div>
          </div>
          {submissionId && (
            <div className="mt-4 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded text-sm text-emerald-800">
              ✅ Submission saved: <span className="font-mono">{submissionId}</span>
            </div>
          )}
        </div>

        {/* Form */}
        {config && <FormRenderer config={config} values={values} onChange={(qid, v) => setValues((s) => ({ ...s, [qid]: v }))} />}
      </div>
    </div>
  );
}
