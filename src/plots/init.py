from datetime import datetime
from numpy import isnan
from scipy.stats import kendalltau

from ..models.db import Workflow, Dependency


def compute_vals(workflows: dict[str, Workflow]) -> dict[str, dict[str, list[float]]]:
    results: dict[str, dict[str, list[float]]] = {}

    for workflow_name, workflow in workflows.items():
        shas: list[str] = []
        dates: list[datetime] = []
        actions: list[int] = []
        # dependencies
        direct: list[int] = []
        direct_vuln: list[int] = []
        direct_dev: list[int] = []
        direct_dev_vuln: list[int] = []
        direct_opt: list[int] = []
        direct_opt_vuln: list[int] = []
        indirect: list[int] = []
        indirect_vuln: list[int] = []
        count:  list[int] = []
        count_vuln:  list[int] = []
        # action changes
        user_action_changes: list[int] = []
        non_user_action_upgrades: list[int] = []
        non_user_action_downgrades: list[int] = []
        dependencies_abs_diff: list[int] = []
        vuln_dependencies_abs_diff: list[int] = []
        dependencies_prop_diff: list[float] = []
        vuln_dependencies_prop_diff: list[float] = []
        # action version type
        major: list[int] = []
        complete: list[int] = []
        hash: list[int] = []

        pos = -1
        prev_dependencies_count = 0
        vuln_prev_dependencies_count = 0
        prev_user_versions: dict[str, Dependency] = {}

        for commit_name, commit in workflow.commits.items():
            dates.append(commit.date)
            shas.append(commit_name)
            
            direct_deps = commit.dependencies["direct"].values()
            indirect_deps = commit.dependencies["indirect"].values()
            vuln_indirect_deps = list(filter(lambda el: len(el.vulnerabilities) > 0, indirect_deps))
            
            count.append(len(indirect_deps))
            count_vuln.append(len(vuln_indirect_deps))
            
            direct.append(len(list(filter(lambda el: el.subtype == "direct", indirect_deps))))
            direct_vuln.append(len(list(filter(lambda el: el.subtype == "direct", vuln_indirect_deps))))
            direct_dev.append(len(list(filter(lambda el: el.subtype == "direct_dev", indirect_deps))))
            direct_dev_vuln.append(len(list(filter(lambda el: el.subtype == "direct_dev", vuln_indirect_deps))))
            direct_opt.append(len(list(filter(lambda el: el.subtype == "direct_opt", indirect_deps))))
            direct_opt_vuln.append(len(list(filter(lambda el: el.subtype == "direct_opt", vuln_indirect_deps))))
            indirect.append(len(list(filter(lambda el: el.subtype == "indirect", indirect_deps))))
            indirect_vuln.append(len(list(filter(lambda el: el.subtype == "indirect", vuln_indirect_deps))))
            
            major.append(len(list(filter(lambda el: el.version_type == "major", direct_deps))))
            complete.append(len(list(filter(lambda el: el.version_type == "complete", direct_deps))))
            hash.append(len(list(filter(lambda el: el.version_type == "hash", direct_deps))))

            actions.append(len(direct_deps))

            abs_diff = 0
            vuln_abs_diff = 0
            dependencies_diff = 1.0
            vuln_dependencies_diff = 1.0

            if prev_dependencies_count != 0:
                dependencies_diff = round(
                    (len(indirect_deps) - prev_dependencies_count)
                    / prev_dependencies_count,
                    2,
                )
                abs_diff = len(indirect_deps) - prev_dependencies_count
            elif prev_dependencies_count == 0 and len(indirect_deps) == 0:
                dependencies_diff = 0

            if vuln_prev_dependencies_count != 0:
                vuln_dependencies_diff = round(
                    (len(vuln_indirect_deps) - vuln_prev_dependencies_count)
                    / vuln_prev_dependencies_count,
                    2,
                )
                vuln_abs_diff = len(vuln_indirect_deps) - vuln_prev_dependencies_count
            elif vuln_prev_dependencies_count == 0 and len(vuln_indirect_deps) == 0:
                vuln_dependencies_diff = 0
                
            changes = 0
            non_user_upgrades = 0
            non_user_downgrades = 0
                
            for name, dep in commit.dependencies["direct"].items():
                if name in prev_user_versions:
                    prev = prev_user_versions[name]
                    changes += 1 if dep.version != prev.version else 0
                    
                    if dep.date and prev.date:
                        non_user_upgrades += 1 if dep.version == prev.version and dep.date > prev.date else 0
                        non_user_downgrades -= 1 if dep.version == prev.version and dep.date < prev.date else 0
            
                prev_user_versions[name] = dep

            dependencies_abs_diff.append(abs_diff)
            dependencies_prop_diff.append(dependencies_diff)
            prev_dependencies_count = len(indirect_deps)
            vuln_dependencies_abs_diff.append(vuln_abs_diff)
            vuln_dependencies_prop_diff.append(vuln_dependencies_diff)
            vuln_prev_dependencies_count = len(vuln_indirect_deps)
            
            if pos != -1:
                user_action_changes.append(changes)
                non_user_action_upgrades.append(non_user_upgrades)
                non_user_action_downgrades.append(non_user_downgrades)
                    
            pos += 1
        
        user_action_changes.append(0)
        non_user_action_upgrades.append(0)
        non_user_action_downgrades.append(0)

        actions_diff = [actions[0]] + [
            actions[i] - actions[i - 1] for i in range(1, len(actions))
        ]
        
        tau, pvalue = kendalltau(dates, count_vuln)

        results[workflow_name] = {
            "shas": shas,
            "dates": dates,
            "dependencies": {
                "direct": direct,
                "direct_vuln": direct_vuln,
                "direct_dev": direct_dev,
                "direct_dev_vuln": direct_dev_vuln,
                "direct_opt": direct_opt,
                "direct_opt_vuln": direct_opt_vuln,
                "indirect": indirect,
                "indirect_vuln": indirect_vuln,
            },
            "actions_diff": actions_diff,
            "actions_changes": user_action_changes,
            "non_user_action_upgrades": non_user_action_upgrades,
            "non_user_action_downgrades": non_user_action_downgrades,
            "dependencies_abs_diff": dependencies_abs_diff,
            "dependencies_prop_diff": dependencies_prop_diff,
            "vuln_dependencies_abs_diff": vuln_dependencies_abs_diff,
            "vuln_dependencies_prop_diff": vuln_dependencies_prop_diff,
            # "trend": polyfit(x=[i+1 for i in range(len(count_vuln))], y=count_vuln, deg=1)[-2]
            "trend": [tau if not isnan(tau) else 0.0, pvalue if not isnan(pvalue) else 0.0]
        }

    return results
