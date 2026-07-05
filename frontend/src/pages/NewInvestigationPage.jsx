import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { uploadInvestigation } from "../api/upload";

export function NewInvestigationPage() {
  const navigate = useNavigate();
  const [companyName, setCompanyName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [files, setFiles] = useState([]);

  const mutation = useMutation({
    mutationFn: uploadInvestigation,
    onSuccess: (data) => {
      navigate(`/investigations/${data.investigation_id}/processing`);
    },
  });

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files ?? []));
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!companyName.trim()) return;
    mutation.mutate({ companyName: companyName.trim(), files, websiteUrl: websiteUrl.trim() });
  };

  const canSubmit = companyName.trim().length > 0 && !mutation.isPending;

  return (
    <PageWrapper className="max-w-2xl">
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-wide text-brand">
          New investigation
        </p>
        <h1 className="mt-1 font-display text-3xl font-semibold text-ink">Start digging</h1>
        <p className="mt-2 text-sm text-ink-muted">
          Name the company, then give us at least one lead: a document, a website, or both. The
          AI fills in the rest from public sources.
        </p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <div>
            <label htmlFor="company_name" className="text-sm font-medium text-ink">
              Company name
            </label>
            <input
              id="company_name"
              type="text"
              required
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g. Acme Robotics"
              className="mt-1.5 w-full rounded-lg border border-line bg-surface px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-faint focus:border-brand focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="website_url" className="text-sm font-medium text-ink">
              Website URL <span className="font-normal text-ink-faint">(optional)</span>
            </label>
            <input
              id="website_url"
              type="url"
              value={websiteUrl}
              onChange={(e) => setWebsiteUrl(e.target.value)}
              placeholder="https://company.com"
              className="mt-1.5 w-full rounded-lg border border-line bg-surface px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-faint focus:border-brand focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="documents" className="text-sm font-medium text-ink">
              Documents <span className="font-normal text-ink-faint">(optional)</span>
            </label>
            <label
              htmlFor="documents"
              className="mt-1.5 flex cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border border-dashed border-line-strong bg-paper px-4 py-8 text-center hover:border-brand"
            >
              <span className="text-sm font-medium text-ink">Click to add PDFs</span>
              <span className="text-xs text-ink-faint">
                Annual reports, financial statements, pitch decks, ESG reports
              </span>
            </label>
            <input
              id="documents"
              type="file"
              accept="application/pdf"
              multiple
              onChange={handleFileChange}
              className="sr-only"
            />

            {files.length > 0 && (
              <ul className="mt-3 flex flex-col gap-2">
                {files.map((file, index) => (
                  <li
                    key={`${file.name}-${index}`}
                    className="flex items-center justify-between rounded-md border border-line bg-paper px-3 py-2 text-sm"
                  >
                    <span className="truncate text-ink">{file.name}</span>
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="ml-3 shrink-0 text-xs font-medium text-ink-faint hover:text-risk-critical"
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {mutation.isError && (
            <p className="text-sm text-risk-critical">{mutation.error?.message}</p>
          )}

          <Button type="submit" size="lg" isLoading={mutation.isPending} disabled={!canSubmit}>
            {mutation.isPending ? "Starting investigation…" : "Start investigation"}
          </Button>
        </form>
      </Card>
    </PageWrapper>
  );
}
