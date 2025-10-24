from neo4j import GraphDatabase, Session
from neo4j.exceptions import ServiceUnavailable

from ..models.db import Dependency


PER_PAGE = 1000


def connect(env: dict[str, str]) -> Session:
    URI: str = str(env["NEO_URI"])
    AUTH: tuple[str, str] = (str(env["NEO_USER"]), str(env["NEO_PASS"]))

    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)
        session = driver.session()
        
        session.run("Match () Return 1 Limit 1")

        return session
    except ServiceUnavailable:
        return None
    

def get_all_repositories(session: Session) -> list[str]:
    repositories = session.run(
        """
        MATCH (r:Repository)
        RETURN r.full_name AS repo
        """,
    )
    
    return [repo["repo"] for repo in repositories]


def get_repository_workflows(repository: str, session: Session, page: int = 1) -> list[str]:
    repositories = session.run(
        """
        MATCH (r:Repository {full_name: $repo})-[]->(w:Workflow)
        RETURN w.name AS workflows
        SKIP $skip
        LIMIT $limit
        """,
        repo=repository,
        skip=(page - 1) * PER_PAGE,
        limit=PER_PAGE,
    )

    return [repository["workflows"] for repository in repositories]


def get_workflow_commits(workflow: str,session: Session, page: int = 1) -> list[dict[str, str]]:
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


def get_commit_dependencies(full_commit: str, session: Session) -> dict[str, dict[str, Dependency]]:
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
        MATCH (d:Component)-[]->(dv:Version)<-[ui:USES]-(ac:Commit)<-[*]-(a:Component)
        MATCH (c:Commit {full_name: $commit})-[:USES]->(ac)
        OPTIONAL MATCH (dv)-[:VULNERABLE_TO]->(v:Vulnerability)
        RETURN DISTINCT
          a.full_name as a_name,
          d.full_name AS id_name,
          dv.name AS id_version,
          ui.type AS id_type,
          collect(DISTINCT v) AS vulnerabilities
        """,
        commit=full_commit,
    )

    for indirect_dep in indirect_deps:
        dependencies["indirect"][indirect_dep["id_name"]] = Dependency(
            indirect_dep["a_name"],
            "",
            1,
            indirect_dep["id_version"],
            "",
            indirect_dep["id_type"],
            None,
            indirect_dep["vulnerabilities"],
        )

    return dependencies
