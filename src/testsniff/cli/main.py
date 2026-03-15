from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from testsniff.cli.arguments import ScanCommandArgs
from testsniff.config.types import Confidence, OutputFormat, Severity
from testsniff.reporting.render import render_result
from testsniff.services.scan import ScanRequest, run_scan

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.callback()
def root() -> None:
    """testsniff command group."""


@app.command()
def scan(
    paths: Annotated[list[Path] | None, typer.Argument()] = None,
    output_format: Annotated[
        OutputFormat | None,
        typer.Option("--format", "-f", help="Output format: human, compact, or json."),
    ] = None,
    select: Annotated[
        list[str] | None,
        typer.Option("--select", help="Only run the specified rule IDs."),
    ] = None,
    ignore: Annotated[
        list[str] | None,
        typer.Option("--ignore", help="Skip the specified rule IDs."),
    ] = None,
    minimum_confidence: Annotated[
        Confidence | None,
        typer.Option("--minimum-confidence", help="Minimum confidence to include in output."),
    ] = None,
    minimum_severity: Annotated[
        Severity | None,
        typer.Option("--minimum-severity", help="Minimum severity to include in output."),
    ] = None,
) -> None:
    """Scan target paths for supported test smells."""
    args = ScanCommandArgs(
        paths=tuple(paths or ()),
        output_format=output_format,
        select=tuple(select) if select else None,
        ignore=tuple(ignore) if ignore else None,
        minimum_confidence=minimum_confidence,
        minimum_severity=minimum_severity,
    )

    result = run_scan(
        ScanRequest(
            paths=args.paths,
            paths_explicit=bool(paths),
            overrides=args.to_overrides(),
        )
    )
    typer.echo(render_result(result, args.output_format or result.config.output_format), nl=False)
    raise typer.Exit(code=result.exit_code)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
