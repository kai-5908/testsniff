from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from time import perf_counter

from testsniff import __version__
from testsniff.config.loader import load_scan_config
from testsniff.config.types import ConfigOverrides, ScanConfig
from testsniff.parser.loader import load_source
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding, ParseFailure
from testsniff.reporting.render import resolve_exit_code, sort_findings
from testsniff.rules.registry import get_enabled_rules


@dataclass(slots=True)
class ScanRequest:
    paths: tuple[Path, ...]
    paths_explicit: bool
    overrides: ConfigOverrides


@dataclass(slots=True)
class ScanResult:
    config: ScanConfig
    findings: list[Finding]
    parse_failures: list[ParseFailure]
    files_scanned: int
    files_skipped: int
    elapsed_ms: float
    exit_code: int
    version: str = __version__


def run_scan(request: ScanRequest, cwd: Path | None = None) -> ScanResult:
    cwd = cwd or Path.cwd()
    started_at = perf_counter()
    config = load_scan_config(cwd, _with_request_paths(request))
    rules = get_enabled_rules(config)

    findings: list[Finding] = []
    parse_failures: list[ParseFailure] = []
    files_scanned = 0
    files_skipped = 0

    for path in resolve_target_files(cwd, request.paths, request.paths_explicit, config):
        try:
            source = load_source(path)
            module = ModuleContext.from_source(path, source)
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            parse_failures.append(ParseFailure(path=str(path), message=str(exc)))
            continue

        files_scanned += 1
        for rule in rules:
            findings.extend(rule.analyze(module))

    filtered_findings = _filter_findings(sort_findings(_prefer_specific_rules(findings)), config)
    elapsed_ms = (perf_counter() - started_at) * 1000
    exit_code = resolve_exit_code(filtered_findings, parse_failures)
    return ScanResult(
        config=config,
        findings=filtered_findings,
        parse_failures=parse_failures,
        files_scanned=files_scanned,
        files_skipped=files_skipped,
        elapsed_ms=elapsed_ms,
        exit_code=exit_code,
    )


def resolve_target_files(
    cwd: Path,
    request_paths: tuple[Path, ...],
    paths_explicit: bool,
    config: ScanConfig,
) -> list[Path]:
    roots = request_paths or tuple(Path(path) for path in config.target_paths)
    files: list[Path] = []

    for root in roots:
        resolved_root = root if root.is_absolute() else cwd / root
        if not resolved_root.exists():
            if paths_explicit:
                raise FileNotFoundError(f"Target path does not exist: {root}")
            continue
        if resolved_root.is_file():
            if _matches_target(resolved_root, cwd, config):
                files.append(resolved_root)
            continue
        for candidate in resolved_root.rglob("*.py"):
            if _matches_target(candidate, cwd, config):
                files.append(candidate)
    return sorted(set(files))


def _matches_target(path: Path, cwd: Path, config: ScanConfig) -> bool:
    if path.is_absolute():
        try:
            relative_str = path.relative_to(cwd).as_posix()
        except ValueError:
            relative_str = path.as_posix()
    else:
        relative_str = path.as_posix()
    if any(fnmatch(relative_str, pattern) for pattern in config.exclude_patterns):
        return False
    if any(fnmatch(path.name, pattern) for pattern in config.include_patterns):
        return True
    return False


def _with_request_paths(request: ScanRequest) -> ConfigOverrides:
    if request.paths_explicit:
        return ConfigOverrides(
            output_format=request.overrides.output_format,
            selected_rule_ids=request.overrides.selected_rule_ids,
            ignored_rule_ids=request.overrides.ignored_rule_ids,
            minimum_confidence=request.overrides.minimum_confidence,
            minimum_severity=request.overrides.minimum_severity,
            target_paths=tuple(str(path) for path in request.paths),
        )
    return request.overrides


def _filter_findings(findings: list[Finding], config: ScanConfig) -> list[Finding]:
    return [
        finding
        for finding in findings
        if _meets_confidence_threshold(finding.confidence, config.minimum_confidence)
        and _meets_severity_threshold(finding.severity, config.minimum_severity)
    ]


def _prefer_specific_rules(findings: list[Finding]) -> list[Finding]:
    ts002_locations = {
        (finding.path, finding.line, finding.column)
        for finding in findings
        if finding.rule_id == "TS002"
    }
    if not ts002_locations:
        return findings
    return [
        finding
        for finding in findings
        if not (
            finding.rule_id == "TS001"
            and (finding.path, finding.line, finding.column) in ts002_locations
        )
    ]


def _meets_confidence_threshold(candidate: str, threshold: str) -> bool:
    order = {"medium": 0, "high": 1}
    return order[candidate] >= order[threshold]


def _meets_severity_threshold(candidate: str, threshold: str) -> bool:
    order = {"info": 0, "warning": 1, "error": 2}
    return order[candidate] >= order[threshold]
