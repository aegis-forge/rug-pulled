from datetime import datetime, timedelta

from .neo import Dependency


class Fix:
    sha: str
    date: datetime
    versions: list[str]
    dep_fix_date: datetime | None

    def __init__(
        self,
        sha: str,
        date: datetime,
        versions: list[str],
        dep_fix_date: datetime | None,
    ) -> None:
        self.sha = sha
        self.date = date
        self.versions = versions
        self.dep_fix_date = dep_fix_date


class ActualFix(Fix):
    version_type: str | None
    ttx: timedelta
    ttxa: timedelta | None
    who: str

    def __init__(
        self,
        sha: str,
        version: list[str],
        version_type: str | None,
        date: datetime,
        ttx: timedelta,
        who: str,
        dep_fix_date: datetime | None = None,
        ttxa: timedelta | None = None,
    ) -> None:
        super().__init__(sha, date, version, dep_fix_date)
        self.version_type = version_type
        self.ttx = ttx
        self.ttxa = ttxa
        self.who = who


class PotentialFix(Fix):
    dependencies: bool
    ttpf: timedelta
    ttpfa: timedelta | None

    def __init__(
        self,
        sha: str,
        date: datetime,
        versions: list[str],
        ttpf: timedelta,
        ttpfa: timedelta | None = None,
        dep_fix_date: datetime | None = None,
        dependencies: bool = False,
    ) -> None:
        super().__init__(sha, date, versions, dep_fix_date)
        self.ttpf = ttpf
        self.ttpfa = ttpfa
        self.dependencies = dependencies


class Rugpull:
    location: str
    from_commit: str
    links: tuple[str, str]
    action: tuple[str, Dependency]
    vulnerabilities: dict[str, Dependency]
    introduced: datetime
    downgrade: bool
    fix: Fix | None

    def __init__(
        self,
        location: str,
        from_commit: str,
        links: tuple[str, str],
        action: tuple[str, Dependency],
        vulnerabilities: dict[str, Dependency],
        introduced: datetime,
        downgrade: bool,
        fix: Fix | None = None,
    ) -> None:
        self.location = location
        self.from_commit = from_commit
        self.links = links
        self.action = action
        self.vulnerabilities = vulnerabilities
        self.introduced = introduced
        self.downgrade = downgrade
        self.fix = fix

    def get_fix_category(self) -> str:
        if type(self.fix) is ActualFix:
            return "fixed"
        elif type(self.fix) is PotentialFix:
            return "dep_fixable" if self.fix.dependencies else "fixable"
        else:
            return "unfixable"
