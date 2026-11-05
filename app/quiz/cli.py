"""`quiz` 명령 진입점(design.md 7.2)."""

import argparse

from quiz import db
from quiz.migrate import apply_migrations, current_version


def cmd_migrate(args: argparse.Namespace) -> int:
    from quiz.backup import backup

    if (b := backup(db.db_path(), "migrate")):
        print(f"backup={b}")
    with db.connect() as conn:
        applied = apply_migrations(conn)
        print(f"applied={applied} schema_version={current_version(conn)} db={db.db_path()}")
    return 0


def cmd_snapshot_fetch(args: argparse.Namespace) -> int:
    from datetime import date

    from quiz.allowlist import MANIFEST_PATH, record_fetch
    from quiz.snapshots import fetch_docs_sync, snapshot_name

    today = date.today().isoformat()

    def done(page: str, sha: str) -> None:
        record_fetch(MANIFEST_PATH, snapshot_name(page), sha, today)
        print(f"{snapshot_name(page)} sha256={sha}", flush=True)

    _, errors = fetch_docs_sync(args.pages, done)
    for page, err in errors.items():
        print(f"error: {page}: {err}")
    return 1 if errors else 0


def cmd_snapshot_fetch_ref(args: argparse.Namespace) -> int:
    from datetime import date

    from quiz.allowlist import MANIFEST_PATH, record_fetch
    from quiz.snapshots import fetch_refs_sync, ref_snapshot_name

    today = date.today().isoformat()

    def done(url: str, sha: str) -> None:
        record_fetch(MANIFEST_PATH, ref_snapshot_name(url), sha, today)
        print(f"{ref_snapshot_name(url)} sha256={sha}", flush=True)

    _, errors = fetch_refs_sync(args.urls, done)
    for url, err in errors.items():
        print(f"error: {url}: {err}")
    return 1 if errors else 0


def cmd_allowlist_build(args: argparse.Namespace) -> int:
    from quiz import allowlist

    rows = allowlist.parse_page_table(allowlist.PAGE_ALLOWLIST_MD.read_text(encoding="utf-8"))
    try:
        out = allowlist.build(rows, allow_missing=args.allow_missing)
    except allowlist.AllowlistError as e:
        print(f"error: {e}")
        return 1
    allowlist.write_yaml(out)
    have = sum(1 for r in out if r["snapshot"])
    print(f"rows={len(out)} with_snapshot={have} missing={len(out) - have} path={allowlist.ALLOWLIST_PATH}")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    from quiz.batch import run_batch, unfinished
    from quiz.env import load_cli_env

    load_cli_env()
    batch_id = run_batch(plan=args.plan, count=args.count, resume=args.resume)
    left = unfinished(batch_id)
    print(f"batch_id={batch_id} unfinished={left}")
    if left:
        print(f"resume: uv run quiz generate --resume {batch_id}")
    return 1 if left else 0


def cmd_crosscheck(args: argparse.Namespace) -> int:
    from quiz import crosscheck
    from quiz.env import load_cli_env

    load_cli_env()
    try:
        path = crosscheck.run(pool_id=args.pool, batch_id=args.batch, include_code=args.include_code)
    except crosscheck.CrosscheckRegionError as e:
        print(f"error: {e}")
        return 1
    print(path.with_suffix(".md").read_text(encoding="utf-8"))
    print(f"file={path}")
    return 0


def cmd_pool_freeze(args: argparse.Namespace) -> int:
    from quiz.pool import freeze

    with db.connect() as conn:
        apply_migrations(conn)
        psid, n = freeze(conn)
    print(f"pool_snapshot_id={psid} questions={n}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quiz")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("migrate", help="마이그레이션 적용").set_defaults(func=cmd_migrate)

    snap = sub.add_parser("snapshot", help="허용 목록 페이지 스냅샷").add_subparsers(dest="snapshot_cmd", required=True)
    fetch = snap.add_parser("fetch", help="docs-langchain MCP에서 문서 페이지를 받는다")
    fetch.add_argument("pages", nargs="+", help="문서 경로. 예: /oss/python/langgraph/graph-api")
    fetch.set_defaults(func=cmd_snapshot_fetch)
    fref = snap.add_parser("fetch-ref", help="reference-langchain MCP get_symbol 출력을 받는다")
    fref.add_argument("urls", nargs="+", help="API 레퍼런스 URL")
    fref.set_defaults(func=cmd_snapshot_fetch_ref)

    al = sub.add_parser("allowlist", help="허용 목록").add_subparsers(dest="allowlist_cmd", required=True)
    build = al.add_parser("build", help="page-allowlist.md 표로 allowlist.yaml을 만들고 스냅샷 해시를 검사한다")
    build.add_argument("--allow-missing", action="store_true", help="스냅샷이 없는 행을 snapshot: null로 둔다")
    build.set_defaults(func=cmd_allowlist_build)

    gen = sub.add_parser("generate", help="문제 생성 배치")
    mode = gen.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", choices=["pilot", "pool", "fill"],
                      help="pilot: 버킷당 1문제(6), pool: 60슬롯, fill: passed가 버킷당·형식마다 10개에 모자란 만큼")
    mode.add_argument("--resume", metavar="BATCH_ID", help="passed·dropped가 아닌 슬롯만 다시 돈다")
    gen.add_argument("--count", type=int, help="슬롯 계획 앞에서 N개만 쓴다")
    gen.set_defaults(func=cmd_generate)

    cc = sub.add_parser("crosscheck", help="T2.10 교차 풀이 점검(Claude 밖 모델 2개, 정답 키 비공개)")
    target = cc.add_mutually_exclusive_group(required=True)
    target.add_argument("--pool", metavar="POOL_SNAPSHOT_ID")
    target.add_argument("--batch", metavar="BATCH_ID")
    cc.add_argument("--include-code", action="store_true", help="코드형도 푼다(기본은 건너뜀)")
    cc.set_defaults(func=cmd_crosscheck)

    pool = sub.add_parser("pool", help="풀 스냅샷").add_subparsers(dest="pool_cmd", required=True)
    pool.add_parser("freeze", help="passed 문제로 풀 스냅샷을 만든다").set_defaults(func=cmd_pool_freeze)

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
