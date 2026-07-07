import { useState } from "react";
import { Button } from "../ui/Button";
import { downloadReportPdf } from "../../api/report";

export function ReportDownloadButton({ investigationId, companyName }) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleClick = async () => {
    setIsDownloading(true);
    setErrorMessage(null);
    try {
      const blob = await downloadReportPdf(investigationId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${(companyName || "company").replace(/[^\w.-]+/g, "_")}_due_diligence_report.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setErrorMessage(err?.message || "The report couldn't be generated. Try again.");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="flex flex-col items-start gap-1.5">
      <Button variant="secondary" onClick={handleClick} isLoading={isDownloading}>
        Download report
      </Button>
      {errorMessage && <p className="text-xs text-risk-critical">{errorMessage}</p>}
    </div>
  );
}
