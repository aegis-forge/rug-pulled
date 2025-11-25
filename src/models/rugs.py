from datetime import datetime, timedelta

from .neo import Dependency


class Fix:
    sha: str
    date: datetime
    versions: list[str]

    def __init__(
        self,
        sha: str,
        date: datetime,
        versions: list[str],
    ) -> None:
        self.sha = sha
        self.date = date
        self.versions = versions


class ActualFix(Fix):
    version_type: str | None
    ttf: timedelta
    who: str

    def __init__(
        self,
        sha: str,
        version: list[str],
        version_type: str | None,
        date: datetime,
        ttf: timedelta,
        who: str,
    ) -> None:
        super().__init__(sha, date, version)
        self.version = version
        self.version_type = version_type
        self.ttf = ttf
        self.who = who


class PotentialFix(Fix):
    dependencies: bool
    tff: timedelta

    def __init__(
        self,
        sha: str,
        date: datetime,
        versions: list[str],
        tff: timedelta,
        dependencies: bool = False,
    ) -> None:
        super().__init__(sha, date, versions)
        self.tff = tff
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
            return "fixable" if self.fix.dependencies else "dep_fixable"
        else:
            return "unfixable"
