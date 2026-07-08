import { useParams } from "react-router-dom";
import { InvestigationDetailPage } from "../components/layout/InvestigationDetailPage";
import { RedFlagSection } from "../components/investigation/RedFlagSection";

export function RedFlagsPage() {
  const { id } = useParams();
  return (
    <InvestigationDetailPage id={id} eyebrow="Risk Analysis" title="Red Flags">
      {(investigation) => <RedFlagSection redFlags={investigation.risk_analysis?.red_flags} />}
    </InvestigationDetailPage>
  );
}
