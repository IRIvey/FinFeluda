import { useState } from "react";
import { Button } from "../ui/Button";
import { downloadReportUrl } from "../../api/report";

export function ReportDownloadButton({ investigationId, pdfUrl }) {
  const [isChecking, setIsChecking] = useState(false);
  const [unavailable, setUnavailable] = useState(false);

  const handleClick = async () => {
    if (pdfUrl) {
      window.open(pdfUrl, "_blank", "noopener,noreferrer");
      return;
    }
    setIsChecking(true);
    try {
      const data = await downloadReportUrl(investigationId);
      if (data?.pdf_url) {
        window.open(data.pdf_url, "_blank", "noopener,noreferrer");
      } else {
        setUnavailable(true);
      }
    } catch {
      setUnavailable(true);
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <div className="flex flex-col items-start gap-1.5">
      <Button variant="secondary" onClick={handleClick} isLoading={isChecking}>
        Download report
      </Button>
      {unavailable && (
        <p className="text-xs text-ink-faint">
          The downloadable PDF isn't ready for this investigation yet.
        </p>
      )}
    </div>
  );
}
