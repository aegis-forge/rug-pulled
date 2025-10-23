from os.path import join, dirname, abspath
from dotenv import dotenv_values
from neo4j import GraphDatabase, Session

from ..models.db import Dependency


PER_PAGE = 100


def connect() -> Session:
    params = dotenv_values(
        join(dirname(abspath(__file__)), "../.env")
    )

    URI: str = str(params["NEO_URI"])
    AUTH: tuple[str, str] = (str(params["NEO_USER"]), str(params["NEO_PASS"]))

    driver = GraphDatabase.driver(URI, auth=AUTH)
    session = driver.session()

    return session


def get_all_workflows(session: Session, page: int = 1) -> dict[str, list[str]]:
    repositories = session.run(
        """
        MATCH (r:Repository)-[]->(w:Workflow)
        RETURN r.full_name AS name, collect(w.name) AS workflows
        SKIP $skip
        LIMIT $limit
        """,
        skip=(page - 1) * PER_PAGE,
        limit=PER_PAGE,
    )

    return {repository["name"]: repository["workflows"] for repository in repositories}


def get_workflow_commits(session: Session, page: int = 1) -> dict[str, list[dict[str, str]]]:
    workflows = session.run(
        """
        MATCH (w:Workflow)-[]->(c:Commit)
        WITH w, collect({name: c.name, date: c.date}) AS commits
        RETURN w.full_name AS name, commits
        SKIP $skip
        LIMIT $limit
        """,
        skip=(page - 1) * PER_PAGE,
        limit=PER_PAGE,
    )

    return {workflow["name"]: workflow["commits"] for workflow in workflows}


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
