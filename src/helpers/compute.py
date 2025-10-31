from datetime import datetime
from enum import Enum
from numpy import isnan
from scipy.stats import kendalltau

from ..models.neo import Workflow


def compute_dependencies(workflow: Workflow) -> dict[str, str|datetime]:
    dates: list[datetime] = []
    direct: list[int] = []
    direct_vuln: list[int] = []
    direct_dev: list[int] = []
    direct_dev_vuln: list[int] = []
    direct_opt: list[int] = []
    direct_opt_vuln: list[int] = []
    indirect: list[int] = []
    indirect_vuln: list[int] = []
    
    for commit in workflow.commits.values():
        dates.append(commit.date)
        
        indirect_deps = commit.dependencies["indirect"].values()
        vuln_indirect_deps = list(filter(lambda el: len(el.vulnerabilities) > 0, indirect_deps))

        direct.append(len(list(filter(lambda el: el.subtype == "direct", indirect_deps))))
        direct_vuln.append(len(list(filter(lambda el: el.subtype == "direct", vuln_indirect_deps))))
        direct_dev.append(len(list(filter(lambda el: el.subtype == "direct_dev", indirect_deps))))
        direct_dev_vuln.append(len(list(filter(lambda el: el.subtype == "direct_dev", vuln_indirect_deps))))
        direct_opt.append(len(list(filter(lambda el: el.subtype == "direct_opt", indirect_deps))))
        direct_opt_vuln.append(len(list(filter(lambda el: el.subtype == "direct_opt", vuln_indirect_deps))))
        indirect.append(len(list(filter(lambda el: el.subtype == "indirect", indirect_deps))))
        indirect_vuln.append(len(list(filter(lambda el: el.subtype == "indirect", vuln_indirect_deps))))
        
    return {
        "dates": dates,
        "direct": direct,
        "direct_vuln": direct_vuln,
        "direct_dev": direct_dev,
        "direct_dev_vuln": direct_dev_vuln,
        "direct_opt": direct_opt,
        "direct_opt_vuln": direct_opt_vuln,
        "indirect": indirect,
        "indirect_vuln": indirect_vuln,
    }


def compute_trend(workflow: Workflow) -> dict[str, float]:
    dates: list[datetime] = []
    count_vuln: list[int] = []

    for commit in workflow.commits.values():
        indirect_deps = commit.dependencies["indirect"].values()
        vuln_indirect_deps = list(
            filter(lambda el: len(el.vulnerabilities) > 0, indirect_deps)
        )

        dates.append(commit.date)
        count_vuln.append(len(vuln_indirect_deps))

    tau, pvalue = kendalltau(dates, count_vuln)
    
    return {
        "tau": tau if not isnan(tau) else 0.0,
        "pvalue": pvalue if not isnan(pvalue) else 0.0,
    }
    

def compute_trend_category(tau: float, pvalue: float, threshold: float) -> dict[str, str]:
    trend_type = ":material/equal:"
    trend_color = "gray"
    
    if pvalue <= threshold:
        if -1 <= tau < -.5:
            trend_type = ":material/keyboard_double_arrow_down:"
            trend_color = "green"
        elif -.5 <= tau < 0:
            trend_type = ":material/keyboard_arrow_down:"
            trend_color = "green"
        elif 0 < tau <= .5:
            trend_type = ":material/keyboard_arrow_up:"
            trend_color = "red"
        elif .5 < tau <= 1:
            trend_type = ":material/keyboard_double_arrow_up:"
            trend_color = "red"
        
    return {
        "type": trend_type,
        "color": trend_color,
    }
