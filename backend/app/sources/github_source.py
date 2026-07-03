"""
GitHub fetcher. Free public API (60/hr unauthenticated, higher with
optional GITHUB_TOKEN). Catches engineering activity signal.
"""
import httpx
from datetime import datetime, timezone
from app.sources.base import BaseFetcher
from app.schemas.source_document import SourceDocument, SourceType


class GitHubFetcher(BaseFetcher):
    source_type = SourceType.GITHUB

    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        github_token = kwargs.get("github_token")
        headers = {"Accept": "application/vnd.github+json"}
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        org_slug = company_name.lower().replace(" ", "")

        async with httpx.AsyncClient(timeout=self.timeout_seconds, headers=headers) as client:
            org_resp = await client.get(f"https://api.github.com/orgs/{org_slug}")

            if org_resp.status_code != 200:
                search_resp = await client.get(
                    "https://api.github.com/search/users",
                    params={"q": f"{company_name} type:org", "per_page": 1},
                )
                search_resp.raise_for_status()
                items = search_resp.json().get("items", [])
                if not items:
                    return SourceDocument(
                        source_type=self.source_type,
                        source_name="GitHub",
                        raw_text="",
                        fetch_succeeded=False,
                        fetch_error="no matching organization found",
                    )
                org_slug = items[0]["login"]
                org_resp = await client.get(f"https://api.github.com/orgs/{org_slug}")
                org_resp.raise_for_status()

            org = org_resp.json()

            repos_resp = await client.get(
                f"https://api.github.com/orgs/{org_slug}/repos",
                params={"sort": "pushed", "per_page": 10},
            )
            repos = repos_resp.json() if repos_resp.status_code == 200 else []

            most_recent_push = None
            repo_lines = []
            for r in repos:
                pushed_at = r.get("pushed_at")
                if pushed_at:
                    dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                    if most_recent_push is None or dt > most_recent_push:
                        most_recent_push = dt
                repo_lines.append(
                    f"- {r.get('name')}: {r.get('stargazers_count', 0)} stars, "
                    f"language={r.get('language')}, last pushed {pushed_at}"
                )

            days_since_last_push = (
                (datetime.now(timezone.utc) - most_recent_push).days
                if most_recent_push else None
            )

            text = (
                f"GitHub organization: {org.get('login')}\n"
                f"Public repos: {org.get('public_repos')}\n"
                f"Followers: {org.get('followers')}\n"
                f"Created: {org.get('created_at')}\n"
                f"Most recent push across top repos: {most_recent_push} "
                f"({days_since_last_push} days ago)\n\n"
                f"Top repositories by recent activity:\n" + "\n".join(repo_lines)
            )

            return SourceDocument(
                source_type=self.source_type,
                source_name="GitHub",
                origin_url=org.get("html_url"),
                title=org.get("login"),
                raw_text=text,
                fetch_succeeded=True,
                extra_metadata={"days_since_last_push": days_since_last_push},
            )