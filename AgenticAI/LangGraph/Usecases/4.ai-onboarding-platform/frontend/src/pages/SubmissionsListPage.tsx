import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import StatusBadge from "../components/StatusBadge";
import { listSubmissions } from "../lib/api";
import type { Submission } from "../types/api";

export default function SubmissionsListPage() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listSubmissions()
      .then(setSubmissions)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader title="My Submissions" subtitle="All client submissions you've created" />
      <div className="p-8">
        {loading && <p className="text-slate-500">Loading...</p>}
        {!loading && submissions.length === 0 && (
          <p className="text-slate-500">No submissions yet. Fill out a form to get started.</p>
        )}
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-4 py-3 font-semibold text-slate-700">Submission ID</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-700">Client</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-700">Form</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-700">Plan</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-700">Status</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-700">Created</th>
              </tr>
            </thead>
            <tbody>
              {submissions.map((s) => (
                <tr key={s.submission_id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link
                      to={`/submissions/${s.submission_id}`}
                      className="font-mono text-xs text-blue-600 hover:underline"
                    >
                      {s.submission_id}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{s.client_name}</td>
                  <td className="px-4 py-3">{s.form_id}</td>
                  <td className="px-4 py-3">{s.plan_type ?? "—"}</td>
                  <td className="px-4 py-3"><StatusBadge status={s.status} /></td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {s.created_at ? new Date(s.created_at).toLocaleString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
