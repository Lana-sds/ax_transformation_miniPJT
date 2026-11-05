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
    from pathlib import Path

    from quiz import experiments
    from quiz.batch import run_batch, unfinished
    from quiz.env import load_cli_env
    from quiz.pipeline import prompts

    fixed = None
    try:
        # 고정 슬롯이나 변형 프롬프트는 실험이다. data/quiz.db에 쓰지 않는다(04 계획 1-가 7)
        if args.slots or prompts.is_overridden():
            experiments.require_experiment_db()
        if args.slots:
            fixed = experiments.load_slots(Path(args.slots))
    except (experiments.ExperimentError, ValueError) as e:
        print(f"error: {e}")
        return 1
    load_cli_env()
    batch_id = run_batch(plan=args.plan, count=args.count, resume=args.resume, fixed_slots=fixed)
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


def cmd_metrics(args: argparse.Namespace) -> int:
    from quiz import metrics

    with db.connect() as conn:
        apply_migrations(conn)
        path = metrics.write(conn)
    print(f"file={path}")
    return 0


def cmd_experiment_judge(args: argparse.Namespace) -> int:
    import json
    from pathlib import Path

    from quiz import experiments
    from quiz.env import load_cli_env

    load_cli_env()
    try:
        path = experiments.run_judge(Path(args.items), args.arm, model_id=args.model, exp=args.exp)
    except experiments.ExperimentError as e:
        print(f"error: {e}")
        return 1
    results = json.loads(path.read_text(encoding="utf-8"))["results"]
    errors = [r["item_id"] for r in results if r["error"]]
    print(f"file={path} judged={len(results) - len(errors)} errors={len(errors)}")
    if errors:
        print(f"resume: rerun the same command (errors: {', '.join(errors)})")
    return 1 if errors else 0


def cmd_experiment_summary(args: argparse.Namespace) -> int:
    from quiz import experiments

    compare = tuple(args.compare.split(",")) if args.compare else None
    if compare is not None and len(compare) != 2:
        print("error: --compare needs two arm names: a,b")
        return 1
    try:
        print(experiments.render(experiments.summary(args.exp, compare=compare)), end="")
    except experiments.ExperimentError as e:
        print(f"error: {e}")
        return 1
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
    mode.add_argument("--slots", metavar="JSON",
                      help="고정 슬롯 목록 파일(04 실험). QUIZ_DB가 실험 DB를 가리켜야 한다")
    gen.add_argument("--count", type=int, help="슬롯 계획(또는 고정 슬롯) 앞에서 N개만 쓴다")
    gen.set_defaults(func=cmd_generate)

    cc = sub.add_parser("crosscheck", help="T2.10 교차 풀이 점검(Claude 밖 모델 2개, 정답 키 비공개)")
    target = cc.add_mutually_exclusive_group(required=True)
    target.add_argument("--pool", metavar="POOL_SNAPSHOT_ID")
    target.add_argument("--batch", metavar="BATCH_ID")
    cc.add_argument("--include-code", action="store_true", help="코드형도 푼다(기본은 건너뜀)")
    cc.set_defaults(func=cmd_crosscheck)

    pool = sub.add_parser("pool", help="풀 스냅샷").add_subparsers(dest="pool_cmd", required=True)
    pool.add_parser("freeze", help="passed 문제로 풀 스냅샷을 만든다").set_defaults(func=cmd_pool_freeze)

    sub.add_parser("metrics", help="data/metrics/baseline.json을 다시 쓴다").set_defaults(func=cmd_metrics)

    exp = sub.add_parser("experiment", help="04 프롬프트·모델 실험").add_subparsers(dest="experiment_cmd",
                                                                               required=True)
    ej = exp.add_parser("judge", help="생성 없이 Judge만 문항마다 돌려 data/experiments/<EXP>/<arm>.json에 쓴다")
    ej.add_argument("--items", required=True, metavar="JSON", help="문항 목록 파일(quiz/experiments.py 설명)")
    ej.add_argument("--arm", required=True, help="arm 이름. 결과 파일 이름이 된다")
    ej.add_argument("--model", metavar="MODEL_ID", help="Judge 모델 ID. 없으면 NFR-4.2 Judge 모델")
    ej.add_argument("--exp", default="EXP-1", help="실험 ID(기본 EXP-1)")
    ej.set_defaults(func=cmd_experiment_judge)
    es = exp.add_parser("summary", help="arm마다 지표 표를 낸다")
    es.add_argument("--exp", required=True, help="실험 ID. 예: EXP-1, EXP-2")
    es.add_argument("--compare", metavar="A,B", help="EXP-1: 두 arm 사이 판정 뒤집힘 수")
    es.set_defaults(func=cmd_experiment_summary)

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
