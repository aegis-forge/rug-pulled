from ..models.db import Workflow


def _get_data(workflow: Workflow) -> list[list[int]]:
    nodes: list[str] = list(workflow.commits.keys())
    
    # Get all actions, dependencies, and vulnerabilities
    for commit in workflow.commits.values():
        nodes(commit.dependencies.values())
    
    sources = []
    targets = []
    values = []
    
    
    