import { useParams } from "react-router-dom";
import { InvestigationDetailPage } from "../components/layout/InvestigationDetailPage";
import { RecommendationsPanel } from "../components/investigation/RecommendationsPanel";

export function RecommendationsPage() {
  const { id } = useParams();
  return (
    <InvestigationDetailPage id={id} eyebrow="Overview" title="Recommendations">
      {(investigation) => <RecommendationsPanel recommendations={investigation.recommendations} />}
    </InvestigationDetailPage>
  );
}
