from datetime import datetime

from neo4j import GraphDatabase, Session
from requests import post

from ..models.neo import Dependency

PER_PAGE = 1000


def connect(env: dict[str, str]) -> Session:
    URI: str = str(env["NEO_URI"])
    AUTH: tuple[str, str] = (str(env["NEO_USER"]), str(env["NEO_PASS"]))

    driver = GraphDatabase.driver(URI, auth=AUTH)
    session = driver.session()

    return session


def get_all_repositories(session: Session) -> list[str]:
    repositories = session.run(
        """
        MATCH (r:Repository)
        RETURN r.full_name AS repo
        """,
    )

    return [repo["repo"] for repo in repositories]


def get_repository_workflows(
    repository: str, session: Session, page: int = 1
) -> dict[str, str]:
    repositories = session.run(
        """
        MATCH (r:Repository {full_name: $repo})-[]->(w:Workflow)
        RETURN w.name AS workflows, w.path AS path
        SKIP $skip
        LIMIT $limit
        """,
        repo=repository,
        skip=(page - 1) * PER_PAGE,
        limit=PER_PAGE,
    )

    return {repository["workflows"]: repository["path"] for repository in repositories}


def get_workflow_commits(
    workflow: str, session: Session, page: int = 1
) -> list[tuple[str, datetime]]:
    workflows = session.run(
        """
        MATCH (w:Workflow {full_name: $workflow})-[]->(c:Commit)
        RETURN c.name AS name, c.date AS date
        ORDER BY date
        SKIP $skip
        LIMIT $limit
        """,
        workflow=workflow,
        skip=(page - 1) * PER_PAGE,
        limit=PER_PAGE,
    )

    return [(workflow["name"], workflow["date"]) for workflow in workflows]


def get_commit_dependencies(
    full_commit: str, session: Session
) -> dict[str, dict[str, Dependency]]:
    dependencies: dict[str, dict[str, Dependency]] = {"direct": {}, "indirect": {}}

    direct_deps = session.run(
        """
        MATCH (ac:Commit)<-[*]-(a:Component)
        MATCH (:Commit {full_name: $commit})-[u:USES]->(ac)
        OPTIONAL MATCH (ac)-[:VULNERABLE_TO]->(v:Vulnerability)
        RETURN DISTINCT
            u.times AS u_times,
            u.version AS u_version,
            u.type AS u_type,
            ac.name AS c_hash,
            ac.date AS c_date,
            a.full_name AS a_name,
            a.subtype AS a_subtype,
            collect(DISTINCT v) AS vulnerabilities
        """,
        commit=full_commit,
    )

    for direct_dep in direct_deps:
        dependencies["direct"][direct_dep["a_name"]] = Dependency(
            "",
            direct_dep["c_hash"],
            direct_dep["u_times"],
            direct_dep["u_version"],
            direct_dep["u_type"],
            direct_dep["a_subtype"],
            direct_dep["c_date"],
            direct_dep["vulnerabilities"],
        )

    indirect_deps = session.run(
        """
        MATCH (dv:Version)<-[ui:USES]-(ac:Commit)
        MATCH (c:Commit {full_name: $commit})-[:USES]->(ac)
        OPTIONAL MATCH (dv)-[:VULNERABLE_TO]->(v:Vulnerability)
        RETURN DISTINCT
          ac.full_name as a_name,
          dv.full_name AS id_name,
          dv.name AS id_version,
          ui.type AS id_type,
          collect(DISTINCT v) AS vulnerabilities
        """,
        commit=full_commit,
    )

    for indirect_dep in indirect_deps:
        name = "/".join(indirect_dep["id_name"].split("/")[:-1])
        
        dependencies["indirect"][name] = Dependency(
            "/".join(indirect_dep["a_name"].split("/")[:2]),
            "",
            1,
            indirect_dep["id_version"],
            "",
            indirect_dep["id_type"],
            None,
            indirect_dep["vulnerabilities"],
        )

    return dependencies


def get_first_fixed_commit(
    action: str, deps: list[str], date: datetime, session: Session
) -> tuple[datetime, list[str], str] | None:
    commit = session.run(
        """
        MATCH (n:Component {full_name: $action})-[]->(v:Version)-[]->(c:Commit)-[]->(d:Version)
        OPTIONAL MATCH (d)-[]->(vuln:Vulnerability)
        WITH
          v.name AS version,
          c.name AS commit,
          c.date AS date,
          CASE vuln
            WHEN IS NOT NULL THEN split(d.full_name, "/")[0]
            ELSE NULL
          END AS vuln_deps
        WHERE
          c.date IS NOT NULL
          AND c.date > $date
        WITH
          version AS version,
          date AS date,
          commit AS sha,
          COLLECT(DISTINCT vuln_deps) AS vulns
        WHERE none(x IN vulns WHERE x IN $deps)
        RETURN
          date AS date,
          COLLECT(version) AS versions,
          sha AS sha
        ORDER BY date
        LIMIT 1
        """,
        action=action,
        deps=deps,
        date=date,
    )

    result = [
        (version["date"], version["versions"], version["sha"]) for version in commit
    ]

    return result[0] if result else None


def is_dependency_fixable(dependency: str, version: str) -> datetime | None:
    res = post(
        url="https://api.osv.dev/v1/query",
        json={
            "package": {
                "purl": f"pkg:npm/{dependency}@{version}",
            }
        },
    )

    fixed_dates: list[datetime] = []
    fixed_versions: list[str] = []
    
    if "vulns" not in res.json():
        return None

    for vuln in res.json()["vulns"]:
        for affected in vuln["affected"]:
            for range in affected["ranges"]:
                for event in range["events"]:
                    if "fixed" in event:
                        date = datetime.strptime(vuln["published"], "%Y-%m-%dT%H:%M:%SZ")
                        
                        fixed_dates.append(date)
                        fixed_versions.append(event["fixed"])

    return sorted(fixed_dates)[-1] if len(fixed_versions) > 0 else None
