"""`quiz` 명령 진입점(design.md 7.2)."""

import argparse

from quiz import db
from quiz.migrate import apply_migrations, current_version


def cmd_migrate(args: argparse.Namespace) -> int:
    with db.connect() as conn:
        applied = apply_migrations(conn)
        print(f"applied={applied} schema_version={current_version(conn)} db={db.db_path()}")
    return 0


def cmd_snapshot_fetch(args: argparse.Namespace) -> int:
    from quiz.snapshots import fetch_docs_sync, snapshot_name

    for page, sha in fetch_docs_sync(args.pages).items():
        print(f"{snapshot_name(page)} sha256={sha}")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    from quiz.batch import run_batch
    from quiz.env import load_cli_env

    load_cli_env()
    batch_id = run_batch(args.count)
    print(f"batch_id={batch_id}")
    return 0


def cmd_pool_freeze(args: argparse.Namespace) -> int:
    from quiz.pool import freeze

    with db.connect() as conn:
        apply_migrations(conn)
        psid, n = freeze(conn)
    print(f"pool_snapshot_id={psid} questions={n}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="quiz")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("migrate", help="마이그레이션 적용").set_defaults(func=cmd_migrate)

    snap = sub.add_parser("snapshot", help="허용 목록 페이지 스냅샷").add_subparsers(dest="snapshot_cmd", required=True)
    fetch = snap.add_parser("fetch", help="docs-langchain MCP에서 문서 페이지를 받는다")
    fetch.add_argument("pages", nargs="+", help="문서 경로. 예: /oss/python/langgraph/graph-api")
    fetch.set_defaults(func=cmd_snapshot_fetch)

    gen = sub.add_parser("generate", help="문제 생성 배치")
    gen.add_argument("--count", type=int, default=1, help="M0 임시: 단일 선택 슬롯 수")
    gen.set_defaults(func=cmd_generate)

    pool = sub.add_parser("pool", help="풀 스냅샷").add_subparsers(dest="pool_cmd", required=True)
    pool.add_parser("freeze", help="passed 문제로 풀 스냅샷을 만든다").set_defaults(func=cmd_pool_freeze)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
