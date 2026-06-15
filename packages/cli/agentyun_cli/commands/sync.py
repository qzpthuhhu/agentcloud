"""agentyun sync"""
import json
import click
from rich.console import Console

from ._common import DEFAULT_SERVER, get_config, require_creds, print_success, print_info


console = Console()


@click.command("sync")
@click.option("--push-only", is_flag=True, help="Only push local events")
@click.option("--pull-only", is_flag=True, help="Only pull remote events")
@click.option("--server", default=None)
@click.option("--data-dir", default=None)
def sync_cmd(push_only: bool, pull_only: bool, server: str | None, data_dir: str | None):
    """Sync local memory with cloud.

    Default: push then pull (full sync).
    """
    server = server or DEFAULT_SERVER
    cfg = get_config(server, data_dir)
    ac = require_creds(cfg)

    if push_only and pull_only:
        raise click.UsageError("Cannot use --push-only and --pull-only together")

    if push_only:
        pushed = ac.sync.push()
        print_success(f"Pushed {pushed} local events to cloud")
    elif pull_only:
        pulled = ac.sync.pull()
        print_success(f"Pulled {pulled} remote events")
    else:
        result = ac.sync.once()
        print_success(f"Sync complete: pushed={result['pushed']} pulled={result['pulled']}")