"""
main.py  —  Security Layer Entry Point
=======================================
Usage:
    python main.py <path_to_project>           # scan a directory
    python main.py <path_to_project> --json    # output JSON report
    python main.py <path_to_project> --report  # save report to security_report.txt
"""

import sys
import os
import json
import datetime

from utils.file_handler import get_all_files, read_file

from scanner.static_analyzer import scan_static
from scanner.secret_scanner import scan_secrets
from scanner.dependency_scanner import scan_dependencies
from scanner.config_scanner import scan_config
from scanner.ai_analyzer import ai_risk_score

from risk_engine import calculate_risk, risk_breakdown
from decision_engine import make_decision

# ─── ANSI colour helpers ──────────────────────────────────────────────────────
def _c(text, code): return f"\033[{code}m{text}\033[0m"
RED    = lambda t: _c(t, "91")
YELLOW = lambda t: _c(t, "93")
GREEN  = lambda t: _c(t, "92")
CYAN   = lambda t: _c(t, "96")
BOLD   = lambda t: _c(t, "1")
DIM    = lambda t: _c(t, "2")

SEVERITY_COLOR = {
    "CRITICAL": RED,
    "HIGH":     RED,
    "MEDIUM":   YELLOW,
    "LOW":      DIM,
}


def _fmt_issue(issue: dict, file_path: str, base: str) -> str:
    rel = os.path.relpath(file_path, base)
    sev = issue.get("severity", "LOW")
    color = SEVERITY_COLOR.get(sev, DIM)
    line  = f" line {issue['line']}" if issue.get("line") else ""
    snip  = f"  ↳ {issue['snippet']}" if issue.get("snippet") else ""
    return f"  {color(f'[{sev}]')} {issue['description']}\n     File: {rel}{line}\n{snip}"


def run_scan(directory: str, output_json: bool = False, save_report: bool = False):
    if not os.path.exists(directory):
        print(RED(f"Error: '{directory}' does not exist."))
        sys.exit(1)

    if os.path.isfile(directory):
        files = [directory]
    else:
        files = get_all_files(directory)

    if not files:
        if os.path.isdir(directory):
            print(YELLOW("No scannable files found in the given directory."))
        else:
            print(YELLOW(f"File '{directory}' has an unsupported extension or is not scannable."))
        sys.exit(0)

    print(BOLD(f"\n🔍  Scanning {len(files)} file(s) in: {directory}\n"))

    all_file_results = []
    total_risk       = 0.0

    for file_path in files:
        content = read_file(file_path)
        if not content.strip():
            continue

        static_issues = scan_static(content)
        secret_issues = scan_secrets(content)
        dep_issues    = scan_dependencies(file_path, content)
        config_issues = scan_config(file_path, content)
        ai_score      = ai_risk_score(content)

        file_risk = calculate_risk(
            static_issues, secret_issues, dep_issues, config_issues, ai_score
        )
        total_risk = max(total_risk, file_risk)

        all_issues = static_issues + secret_issues + dep_issues + config_issues
        if all_issues or ai_score > 0.3:
            all_file_results.append({
                "file":           file_path,
                "risk":           file_risk,
                "ai_score":       round(ai_score, 3),
                "static_issues":  static_issues,
                "secret_issues":  secret_issues,
                "dep_issues":     dep_issues,
                "config_issues":  config_issues,
            })

    # Sort files by risk descending
    all_file_results.sort(key=lambda r: r["risk"], reverse=True)

    decision    = make_decision(total_risk)
    breakdown   = risk_breakdown(
        [i for r in all_file_results for i in r["static_issues"]],
        [i for r in all_file_results for i in r["secret_issues"]],
        [i for r in all_file_results for i in r["dep_issues"]],
        [i for r in all_file_results for i in r["config_issues"]],
        max((r["ai_score"] for r in all_file_results), default=0.0),
    )

    # ── JSON output mode ──────────────────────────────────────────────────────
    if output_json:
        report = {
            "timestamp":  datetime.datetime.now().isoformat(),
            "directory":  directory,
            "files_scanned": len(files),
            "risk_score": total_risk,
            "decision":   decision.action,
            "breakdown":  breakdown,
            "files":      [
                {
                    "path":    r["file"],
                    "risk":    r["risk"],
                    "issues":  r["static_issues"] + r["secret_issues"] + r["dep_issues"] + r["config_issues"],
                }
                for r in all_file_results
            ],
        }
        out = json.dumps(report, indent=2)
        print(out)
        if save_report:
            fname = "security_report.json"
            with open(fname, "w") as f:
                f.write(out)
            print(f"\nReport saved to {fname}", file=sys.stderr)
        return

    # ── Human-readable output ────────────────────────────────────────────────
    lines = []
    lines.append(BOLD("\n╔══════════════════════════════════════════╗"))
    lines.append(BOLD("║         SECURITY SCAN REPORT             ║"))
    lines.append(BOLD("╚══════════════════════════════════════════╝"))
    lines.append(f"  Scanned : {directory}")
    lines.append(f"  Files   : {len(files)}")
    lines.append(f"  Time    : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append(BOLD("  RISK BREAKDOWN"))
    lines.append(f"  {'Static analysis':<22} {breakdown['static_points']:>6.1f} pts")
    lines.append(f"  {'Secret detection':<22} {breakdown['secret_points']:>6.1f} pts")
    lines.append(f"  {'Dependency audit':<22} {breakdown['dependency_points']:>6.1f} pts")
    lines.append(f"  {'Config audit':<22} {breakdown['config_points']:>6.1f} pts")
    lines.append(f"  {'AI analysis':<22} {breakdown['ai_points']:>6.1f} pts")
    lines.append(f"  {'─'*32}")
    lines.append(BOLD(f"  {'TOTAL RISK SCORE':<22} {total_risk:>6.1f} / 100"))
    lines.append("")

    # Decision banner
    action_color = RED if decision.action == "BLOCK" else (YELLOW if decision.action in ("WARN", "REVIEW") else GREEN)
    lines.append(BOLD(action_color(f"\n  ══  DECISION: {decision.action}  ══")))
    lines.append(f"  {decision.message}\n")

    # Per-file details
    if all_file_results:
        lines.append(BOLD("  ISSUES BY FILE"))
        lines.append("  " + "─" * 60)
        for result in all_file_results:
            rel = os.path.relpath(result["file"], directory)
            risk_str = f"{result['risk']:.1f}"
            rc = RED if result["risk"] >= 45 else (YELLOW if result["risk"] >= 20 else DIM)
            lines.append(f"\n  📄 {CYAN(rel)}  {rc(f'risk={risk_str}')}")
            all_issues = (
                result["static_issues"] +
                result["secret_issues"] +
                result["dep_issues"] +
                result["config_issues"]
            )
            if all_issues:
                for issue in all_issues:
                    lines.append(_fmt_issue(issue, result["file"], directory))
            else:
                lines.append(DIM(f"     AI score: {result['ai_score']} (no pattern issues)"))
    else:
        lines.append(GREEN("\n  ✅  No issues found across scanned files."))

    output = "\n".join(lines) + "\n"
    print(output)

    if save_report:
        # Strip ANSI codes for file output
        import re
        clean = re.sub(r'\033\[[0-9;]*m', '', output)
        fname = "security_report.txt"
        with open(fname, "w") as f:
            f.write(clean)
        print(f"\n  📝 Report saved to {fname}")


# ─── CLI entry point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print("Usage: python main.py <project_path> [--json] [--report]")
        print("       --json    Output results as JSON")
        print("       --report  Save report to file")
        sys.exit(1)

    target    = args[0]
    as_json   = "--json"   in args
    do_report = "--report" in args

    run_scan(target, output_json=as_json, save_report=do_report)