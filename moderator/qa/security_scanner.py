"""Security-focused code analysis"""

from typing import List
from ..models import Issue, CodeOutput


class SecurityScanner:
    """Security-focused code analysis"""

    def scan(self, output: CodeOutput) -> List[Issue]:
        """
        STUB: Would run security tools like bandit, semgrep
        TODO: Integrate actual security scanners
        """
        print("[SecurityScanner] STUB: Would run security scan")
        return []
