from datetime import datetime, timedelta

from .neo import Dependency

class Fix:
    sha: str
    version: str | None
    date: datetime
    ttf: timedelta
    who: str
    
    def __init__(
        self,
        sha: str,
        version: str | None,
        date: datetime,
        ttf: timedelta,
        who: str,
    ) -> None:
        self.sha = sha
        self.version = version
        self.date = date
        self.ttf = ttf
        self.who = who


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
