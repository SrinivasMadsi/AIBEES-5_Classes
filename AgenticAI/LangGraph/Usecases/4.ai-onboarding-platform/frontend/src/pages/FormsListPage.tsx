import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, FileText } from "lucide-react";
import PageHeader from "../components/PageHeader";
import { listForms } from "../lib/api";
import type { FormSummary } from "../types/api";

export default function FormsListPage() {
  const [forms, setForms] = useState<FormSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listForms()
      .then(setForms)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader
        title="Onboarding Forms"
        subtitle="Pick a form to fill out for a client"
      />
      <div className="p-8">
        {loading && <p className="text-slate-500">Loading...</p>}
        {!loading && forms.length === 0 && (
          <p className="text-slate-500">No forms available. Did you run sql/02_seed_forms.sql?</p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl">
          {forms.map((form) => (
            <Link
              key={form.form_id}
              to={`/forms/${form.form_id}/fill`}
              className="bg-white border border-slate-200 rounded-xl p-6 hover:border-blue-400 hover:shadow-md transition-all flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <div className="font-semibold text-slate-900">{form.form_name}</div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    Form ID {form.form_id} · {form.version}
                  </div>
                </div>
              </div>
              <ArrowRight className="w-5 h-5 text-slate-400" />
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
