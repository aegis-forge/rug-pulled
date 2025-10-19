from datetime import datetime
from neotime import DateTime
from neo4j.graph import Node


class Dependency:
    parent: str
    hash: str
    uses: int
    version: str
    version_type: str
    subtype: str
    date: datetime | None
    vulnerabilities: dict[str, dict[str, str]]

    def __init__(
        self,
        parent: str,
        hash: str,
        uses: int,
        version: str,
        version_type: str,
        subtype: str,
        date: DateTime | None,
        vulnerabilities: Node | list[Node],
    ) -> None:
        self.parent = parent
        self.hash = hash
        self.uses = uses
        self.version = version
        self.version_type = version_type
        self.subtype = subtype
        self.vulnerabilities = {}
        self.date = (
            datetime(
                date.year,
                date.month,
                date.day,
                date.hour,
                date.minute,
                date.second,
                tzinfo=date.tzinfo,
            )
            if date
            else None
        )

        if type(vulnerabilities) is list and len(vulnerabilities) > 0:
            for vuln in vulnerabilities:
                self.vulnerabilities[vuln.get("id")] = {}

                for key, value in vuln.items():
                    self.vulnerabilities[vuln.get("id")][key] = value
        elif type(vulnerabilities) is Node:
            self.vulnerabilities[vulnerabilities.get("id")] = {}

            for key, value in vulnerabilities.items():
                self.vulnerabilities[vulnerabilities.get("id")][key] = value


class Commit:
    date: datetime
    dependencies: dict[str, dict[str, Dependency]]

    def __init__(self, date: datetime, dependencies: dict[str, dict[str, Dependency]]) -> None:
        self.date = date
        self.dependencies = dependencies


class Workflow:
    commits: dict[str, Commit]

    def __init__(self, commits: dict[str, Commit]) -> None:
        self.commits = commits
        

class Repository:
    name: str
    workflows: dict[str, Workflow]
    
    def __init__(self, name: str, workflows: dict[str, Workflow]) -> None:
        self.name = name
        self.workflows = workflows
