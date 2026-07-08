import { useParams } from "react-router-dom";
import { InvestigationDetailPage } from "../components/layout/InvestigationDetailPage";
import { ExecutiveSummary } from "../components/investigation/ExecutiveSummary";

export function ExecutiveSummaryPage() {
  const { id } = useParams();
  return (
    <InvestigationDetailPage id={id} eyebrow="Overview" title="Executive Summary">
      {(investigation) => <ExecutiveSummary summary={investigation.executive_summary} />}
    </InvestigationDetailPage>
  );
}
