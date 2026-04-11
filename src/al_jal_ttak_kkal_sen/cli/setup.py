import subprocess
import time
from pathlib import Path

from rich.console import Console


def main() -> None:
    console = Console()
    try:
        _git_submodule_update()
        _pnpm_install()
        _install_postgres()
        _install_pgvector()
        _install_vchord()
        _install_pgrx()
        _install_pg_tokenizer()
        _install_vchord_bm25()
        _setup_postgres()
        _build_opencode_hs()
    except Exception:
        console.print_exception(show_locals=True)


def _setup_postgres() -> None:
    if not _is_postgres_ready():
        _restart_postgres()
    _wait_for_postgres_ready()
    _set_shared_preload_libraries()
    _restart_postgres()
    _wait_for_postgres_ready()
    _create_db()
    _set_search_path()
    _create_vector_extension()
    _create_vchord_extension()
    _create_pg_tokenizer_extension()
    _create_vchord_bm25_extension()
    _create_llmlingua2_tokenizer()


def _build_opencode_hs() -> None:
    cwd = Path("external/hindsight/hindsight-integrations/opencode")
    _run(["npm", "i"], cwd=cwd)
    _run(["npm", "run", "build"], cwd=cwd)


def _git_submodule_update() -> None:
    _run(["git", "submodule", "update", "--init", "--recursive"])


def _pnpm_install() -> None:
    _run(["pnpm", "i"])


def _install_postgres() -> None:
    _run(["brew", "install", "postgresql@18"])


def _install_pgvector() -> None:
    _run(["brew", "install", "pgvector"])


def _install_vchord() -> None:
    cwd = Path("external/VectorChord")
    _run(["make", "build"], cwd=cwd)
    _run(["make", "install"], cwd=cwd)


def _install_pgrx() -> None:
    _run(["cargo", "install", "cargo-pgrx", "--version", "0.16.1", "--locked"])


def _install_pg_tokenizer() -> None:
    cwd = Path("external/pg_tokenizer.rs")
    _pgrx_install(cwd)


def _install_vchord_bm25() -> None:
    cwd = Path("external/VectorChord-bm25")
    _pgrx_install(cwd)


def _pgrx_install(cwd: Path) -> None:
    _run(
        [
            "cargo",
            "pgrx",
            "install",
            "--release",
            "--pg-config",
            "/opt/homebrew/bin/pg_config",
        ],
        cwd=cwd,
    )


def _restart_postgres() -> None:
    _run(["brew", "services", "restart", "postgresql@18"])


def _create_db() -> None:
    result = _run(
        [
            "psql",
            "-h",
            "localhost",
            "-d",
            "postgres",
            "-t",
            "-c",
            "SELECT 1 FROM pg_database WHERE datname='hindsight'",
        ],
        capture_output=True,
    )
    if "1" not in result.stdout:
        _run(["createdb", "hindsight"])


def _is_postgres_ready() -> bool:
    try:
        _run(
            ["pg_isready", "-h", "localhost"],
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        return False
    return True


def _wait_for_postgres_ready() -> None:
    for _ in range(6 * 5):
        if _is_postgres_ready():
            return
        print("Waiting for PostgreSQL to be ready...", flush=True)  # noqa: T201
        time.sleep(10)

    raise RuntimeError("PostgreSQL is not ready after waiting for 5 minutes.")


def _set_shared_preload_libraries() -> None:
    _psql_hs(
        [
            "-c",
            "ALTER SYSTEM SET shared_preload_libraries = vchord,pg_tokenizer;",
        ]
    )


def _set_search_path() -> None:
    _psql_hs(
        [
            "-c",
            "ALTER DATABASE hindsight SET search_path TO "
            '"$user", public, tokenizer_catalog, bm25_catalog;',
        ]
    )


def _create_vector_extension() -> None:
    _psql_hs(
        [
            "-c",
            "CREATE EXTENSION IF NOT EXISTS vector CASCADE;",
        ]
    )


def _create_vchord_extension() -> None:
    _psql_hs(
        [
            "-c",
            "CREATE EXTENSION IF NOT EXISTS vchord CASCADE;",
        ]
    )


def _create_pg_tokenizer_extension() -> None:
    _psql_hs(
        [
            "-c",
            "CREATE EXTENSION IF NOT EXISTS pg_tokenizer CASCADE;",
        ]
    )


def _create_vchord_bm25_extension() -> None:
    _psql_hs(
        [
            "-c",
            "CREATE EXTENSION IF NOT EXISTS vchord_bm25 CASCADE;",
        ]
    )


def _create_llmlingua2_tokenizer() -> None:
    result = _psql_hs(
        [
            "-t",
            "-c",
            "SELECT 1 FROM tokenizer_catalog.tokenizer WHERE name='llmlingua2'",
        ],
        capture_output=True,
    )
    if "1" not in result.stdout:
        _psql_hs(
            [
                "-c",
                "SELECT tokenizer_catalog.create_tokenizer"
                "('llmlingua2', $$model = \"llmlingua2\"$$);",
            ]
        )


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture_output,
        text=True,
        check=True,
    )


def _psql_hs(
    args: list[str], *, capture_output: bool = False
) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            "psql",
            "-h",
            "localhost",
            "-d",
            "hindsight",
            *args,
        ],
        capture_output=capture_output,
    )
