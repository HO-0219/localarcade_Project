#!/usr/bin/env python3
"""Local Arcade 최대 6명 동시 요청 검증 스크립트.

실행 전 백엔드를 시작하고 콘솔에 표시된 6자리 참여 코드를 전달한다.
외부 패키지 없이 Python 표준 라이브러리만 사용한다.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Response:
    ok: bool
    status: int
    elapsed_ms: float
    data: dict[str, Any]


def call(base_url: str, path: str, token: str = "", body: dict[str, Any] | None = None) -> Response:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=payload,
        headers=headers,
        method="GET" if body is None else "POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw) if raw else {}
            return Response(True, response.status, (time.perf_counter() - started) * 1000, data)
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {"error": raw}
        return Response(False, error.code, (time.perf_counter() - started) * 1000, data)
    except Exception as error:  # Network failures must also appear in the report.
        return Response(False, 0, (time.perf_counter() - started) * 1000, {"error": str(error)})


def parallel(jobs: list[tuple], workers: int = 12) -> list[Response]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(call, *job) for job in jobs]
        return [future.result() for future in futures]


def latency_summary(responses: list[Response]) -> dict[str, float]:
    values = [response.elapsed_ms for response in responses]
    ordered = sorted(values)
    p95_index = max(0, min(len(ordered) - 1, int(len(ordered) * 0.95) - 1))
    return {
        "average_ms": round(statistics.mean(values), 2),
        "p95_ms": round(ordered[p95_index], 2),
        "max_ms": round(max(values), 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Local Arcade 최대 6명 동시 요청 검증")
    parser.add_argument("--join-code", required=True, help="백엔드 콘솔의 6자리 참여 코드")
    parser.add_argument("--base-url", default="http://localhost:8081", help="백엔드 주소")
    parser.add_argument("--users", type=int, default=6, choices=range(2, 7), metavar="2-6")
    parser.add_argument("--poll-rounds", type=int, default=5, help="사용자별 상태 조회 반복 횟수")
    parser.add_argument("--report-dir", default="reports", help="Markdown 보고서 저장 폴더")
    args = parser.parse_args()

    print("[1/5] 서버 연결 확인")
    health = call(args.base_url, "/api/state")
    if health.status == 0:
        print(f"  FAIL: 서버에 연결할 수 없습니다: {health.data.get('error')}")
        return 1
    print(f"  OK: HTTP 서버 응답 확인 ({health.status})")

    print(f"[2/5] 테스트 사용자 {args.users}명 동시 입장")
    stamp = datetime.now().strftime("%H%M%S")
    join_jobs = [
        (args.base_url, "/api/join", "", {"code": args.join_code, "nickname": f"T{stamp}{i+1}"})
        for i in range(args.users)
    ]
    join_responses = parallel(join_jobs, workers=args.users)
    tokens = [response.data.get("token", "") for response in join_responses if response.ok]
    if len(tokens) != args.users:
        errors = [response.data.get("error", response.status) for response in join_responses if not response.ok]
        print(f"  FAIL: 성공 {len(tokens)}/{args.users}, 오류={errors}")
        if any("최대 6명" in str(error) for error in errors):
            print("  원인: 브라우저 또는 이전 테스트 사용자가 서버에 아직 접속 중입니다.")
            print("  해결: 브라우저를 닫고 30초 이상 기다리거나, 백엔드를 재시작한 뒤 새 참여 코드로 실행하세요.")
            print("  참고: 백엔드 재시작 시 테스트 플레이어와 세션이 초기화됩니다.")
        return 1
    print(f"  PASS: {len(tokens)}/{args.users}명 입장 성공")

    initial_states = [call(args.base_url, "/api/state", token) for token in tokens]
    initial_credits = {state.data["me"]["id"]: state.data["me"]["credits"] for state in initial_states}

    print(f"[3/5] {args.users}명 야추 참가 요청 동시 실행")
    yacht_jobs = [(args.base_url, "/api/yacht/join", token, {"bet": 100}) for token in tokens]
    yacht_responses = parallel(yacht_jobs, workers=args.users)
    join_success = sum(response.ok for response in yacht_responses)
    social = call(args.base_url, "/api/social/state", tokens[0])
    lobby_count = len(social.data.get("yacht", {}).get("lobby", [])) if social.ok else -1
    after_join_states = [call(args.base_url, "/api/state", token) for token in tokens]
    credits_once = all(
        state.data["me"]["credits"] == initial_credits[state.data["me"]["id"]] - 100
        for state in after_join_states
    )
    concurrent_join_passed = join_success == args.users and lobby_count == args.users and credits_once
    print(
        f"  {'PASS' if concurrent_join_passed else 'FAIL'}: 성공 {join_success}/{args.users}, "
        f"로비 {lobby_count}명, 전원 100 크레딧 1회 차감={credits_once}"
    )

    print("[4/5] 동일 사용자 중복 참가 요청 5건 동시 실행")
    duplicate_jobs = [(args.base_url, "/api/yacht/join", tokens[0], {"bet": 100}) for _ in range(5)]
    duplicate_responses = parallel(duplicate_jobs, workers=5)
    duplicate_success = sum(response.ok for response in duplicate_responses)
    duplicate_rejected = sum(
        (not response.ok) and "이미 참가" in str(response.data.get("error", ""))
        for response in duplicate_responses
    )
    duplicate_state = call(args.base_url, "/api/state", tokens[0])
    duplicate_credit_unchanged = (
        duplicate_state.data["me"]["credits"]
        == initial_credits[duplicate_state.data["me"]["id"]] - 100
    )
    duplicate_passed = duplicate_success == 0 and duplicate_rejected == 5 and duplicate_credit_unchanged
    print(
        f"  {'PASS' if duplicate_passed else 'FAIL'}: 성공 {duplicate_success}, "
        f"중복 거절 {duplicate_rejected}, 추가 차감 없음={duplicate_credit_unchanged}"
    )

    print(f"[5/5] {args.users}명 × 2개 API × {args.poll_rounds}회 동시 상태 조회")
    poll_jobs: list[tuple] = []
    for _ in range(args.poll_rounds):
        for token in tokens:
            poll_jobs.append((args.base_url, "/api/state", token, None))
            poll_jobs.append((args.base_url, "/api/social/state", token, None))
    poll_started = time.perf_counter()
    poll_responses = parallel(poll_jobs, workers=args.users * 2)
    poll_seconds = time.perf_counter() - poll_started
    poll_success = sum(response.ok for response in poll_responses)
    poll_failures = len(poll_responses) - poll_success
    latency = latency_summary(poll_responses)
    polling_passed = poll_failures == 0
    print(
        f"  {'PASS' if polling_passed else 'FAIL'}: {poll_success}/{len(poll_responses)} 성공, "
        f"평균 {latency['average_ms']}ms, p95 {latency['p95_ms']}ms, 최대 {latency['max_ms']}ms"
    )

    # Best-effort cleanup: remove all test users from the yacht lobby.
    parallel([(args.base_url, "/api/yacht/leave", token, {}) for token in tokens], workers=args.users)

    passed = concurrent_join_passed and duplicate_passed and polling_passed
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"local-arcade-concurrency-{datetime.now():%Y%m%d-%H%M%S}.md"
    report = f"""# Local Arcade 동시 요청 테스트 결과

- 실행 시각: {datetime.now():%Y-%m-%d %H:%M:%S}
- 대상 서버: `{args.base_url}`
- 동시 사용자: {args.users}명
- 최종 결과: **{'PASS' if passed else 'FAIL'}**

| 테스트 | 조건 | 결과 | 판정 |
|---|---|---|---|
| 동시 입장 | {args.users}명 동시 `/api/join` | {len(tokens)}/{args.users} 성공 | PASS |
| 동시 게임 참가 | {args.users}명 동시 야추 참가 | 성공 {join_success}, 로비 {lobby_count}명, 100 크레딧 1회 차감={credits_once} | {'PASS' if concurrent_join_passed else 'FAIL'} |
| 중복 요청 방지 | 동일 사용자 참가 요청 5건 | 성공 {duplicate_success}, 중복 거절 {duplicate_rejected}, 추가 차감 없음={duplicate_credit_unchanged} | {'PASS' if duplicate_passed else 'FAIL'} |
| 반복 상태 조회 | {args.users}명 × 2 API × {args.poll_rounds}회 | {poll_success}/{len(poll_responses)} 성공, 실패 {poll_failures} | {'PASS' if polling_passed else 'FAIL'} |

## 응답 시간

- 평균: {latency['average_ms']} ms
- p95: {latency['p95_ms']} ms
- 최대: {latency['max_ms']} ms
- 전체 조회 완료 시간: {poll_seconds:.2f}초

> 이 결과는 동일 LAN 최대 6명이라는 프로젝트 요구사항을 기준으로 한 기능·동시성 검증이며, 대규모 부하 테스트 결과가 아닙니다.
"""
    report_path.write_text(report, encoding="utf-8")
    print(f"\n최종 결과: {'PASS' if passed else 'FAIL'}")
    print(f"보고서: {report_path.resolve()}")
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
