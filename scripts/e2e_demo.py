#!/usr/bin/env python3
"""시연 핵심 시나리오 2개를 실행 중인 스택에 HTTP로 처음부터 끝까지 재현·검증한다.

  python3 scripts/e2e_demo.py                         # http://localhost:5173 (프론트 프록시 경유)
  python3 scripts/e2e_demo.py --base http://localhost:8000 --runs 2 --skip-spa   # 호스트에서 runserver 로 띄운 백엔드 직접

시나리오 1 (회의실): 교육생 로그인 → 이용수칙·현황 확인 → 예약 요청 → 운영팀 목록에서 확인·승인
                    → 교육생 결과(상태·현황·알림) 확인 → (정리) 취소
시나리오 2 (면담):   교육생 로그인 → 유형·가능 시간 → 면담 신청 → 운영팀 담당자 배정·확정(장소)
                    → 교육생 결과(상태·장소·슬롯 마감·알림) 확인 → (정리) 취소

필요 조건: DJANGO_DEBUG=true 인 백엔드(모의 로그인)와 시연 데이터(`manage.py seed_demo`).
표준 라이브러리만 쓰고 비밀값을 다루지 않는다. 각 실행은 자신이 만든 신청·예약을 취소해 되돌려 놓으므로 반복 실행해도 된다.
종료 코드: 0 = 모두 통과, 1 = 실패.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from http.cookiejar import CookieJar
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


class StepFailed(Exception):
    pass


class Api:
    """세션 쿠키·CSRF 를 브라우저처럼 다루는 최소 HTTP 클라이언트."""

    def __init__(self, base: str, label: str) -> None:
        self.base = base.rstrip("/")
        self.label = label
        self.jar = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def _csrf(self) -> str:
        return next((c.value for c in self.jar if c.name == "csrftoken"), "")

    def call(self, method: str, path: str, body=None, expect=(200, 201, 204)):
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Accept": "application/json", "Origin": self.base}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if method != "GET":
            headers["X-CSRFToken"] = self._csrf()
        request = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=20) as response:
                status, raw = response.status, response.read()
        except urllib.error.HTTPError as error:
            status, raw = error.code, error.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            raise StepFailed(
                f"{self.label} {method} {path} → 서버에 연결할 수 없습니다({self.base}). "
                f"스택이 떠 있는지(docker compose up) 확인하세요: {getattr(error, 'reason', error)}"
            ) from error
        payload = None
        if raw:
            try:
                payload = json.loads(raw)
            except ValueError:
                payload = raw.decode(errors="replace")[:200]
        if status not in expect:
            detail = payload if isinstance(payload, dict) else str(payload)[:120]
            raise StepFailed(f"{self.label} {method} {path} → {status} (기대 {list(expect)}) {detail}")
        return payload

    def get(self, path, **kw):
        return self.call("GET", path, **kw)

    def page(self, path: str) -> str:
        """HTML 화면(SPA)을 가져온다."""
        request = urllib.request.Request(self.base + path, headers={"Accept": "text/html"})
        try:
            with self.opener.open(request, timeout=20) as response:
                return response.read().decode(errors="replace")
        except urllib.error.HTTPError as error:
            raise StepFailed(f"{self.label} GET {path} → {error.code}") from error
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            raise StepFailed(f"{self.label} GET {path} → 서버에 연결할 수 없습니다({self.base})") from error

    def post(self, path, body=None, **kw):
        return self.call("POST", path, body, **kw)

    def login(self, role: str) -> None:
        try:
            self.post("/api/auth/mock-login", {"role": role})
        except StepFailed as exc:
            if "→ 404" in str(exc):
                raise StepFailed("모의 로그인이 꺼져 있습니다(백엔드가 DJANGO_DEBUG=false). 개발 모드에서 실행하세요.") from exc
            raise
        self.get("/api/auth/me")  # CSRF 쿠키 발급


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def step(self, name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            raise StepFailed(f"{name}: {detail or '조건 불충족'}")
        self.lines.append(f"    ✓ {name}" + (f"  ({detail})" if detail else ""))


def kst_iso(day: date, hour: int) -> str:
    return datetime(day.year, day.month, day.day, hour, tzinfo=KST).isoformat()


def weekdays_from(offset_start: int, count: int):
    today = datetime.now(KST).date()
    found = []
    offset = offset_start
    while len(found) < count:
        day = today + timedelta(days=offset)
        if day.weekday() < 5:
            found.append(day)
        offset += 1
    return found


# ── 시나리오 1: 회의실 ──────────────────────────────────────────────
def scenario_room(student: Api, staff: Api, r: Report) -> None:
    rules = student.get("/api/rooms/rules")
    r.step("이용수칙을 볼 수 있다", bool(rules["usage_rules"]), f"{len(rules['usage_rules'])}줄")
    rooms = {x["code"]: x for x in student.get("/api/rooms")}
    r.step("장소 3곳이 있다", {"multipurpose", "universe-large", "universe-small"} <= set(rooms))

    room = rooms["multipurpose"]
    chosen = None
    for day in weekdays_from(3, 8):
        availability = student.get(f"/api/rooms/availability?date={day.isoformat()}")
        cells = {h["hour"]: h["state"] for x in availability["rooms"] if x["room"]["id"] == room["id"] for h in x["hours"]}
        for hour in range(rules["open_hour"], rules["close_hour"] - 1):
            if cells.get(hour) == "free" and cells.get(hour + 1) == "free":
                chosen = (day, hour)
                break
        if chosen:
            break
    r.step("예약 가능한 2시간 구간을 찾았다", chosen is not None, f"{chosen[0]:%m.%d} {chosen[1]}시" if chosen else "")
    day, hour = chosen

    created = student.post(
        "/api/reservations",
        {
            "room_id": room["id"],
            "start_at": kst_iso(day, hour),
            "end_at": kst_iso(day, hour + 2),
            "purpose": "E2E 시연 점검",
            "headcount": 3,
        },
    )
    rid = created["id"]
    try:
        r.step("예약을 요청하면 '승인 대기'(pending)다", created["status"] == "pending" and created["conflict"] is False)
        mine = {x["id"]: x for x in student.get("/api/reservations/me")}
        r.step("내 예약 요청 목록에 보인다", mine.get(rid, {}).get("status") == "pending")

        pending = {x["id"]: x for x in staff.get(f"/api/staff/reservations?date={day.isoformat()}&status=pending")}
        r.step("운영팀 목록에 교육생 정보와 함께 보인다", pending.get(rid, {}).get("user", {}).get("intra_id") == "student")

        approved = staff.post(f"/api/staff/reservations/{rid}/approve")
        r.step("운영팀이 승인하면 approved다", approved["status"] == "approved")

        mine = {x["id"]: x for x in student.get("/api/reservations/me")}
        r.step("교육생 화면에서 상태가 '승인됨'으로 바뀐다", mine[rid]["status"] == "approved")
        after = student.get(f"/api/rooms/availability?date={day.isoformat()}")
        row = next(x for x in after["rooms"] if x["room"]["id"] == room["id"])
        states = {h["hour"]: h["state"] for h in row["hours"]}
        r.step("현황표에 '예약 확정'으로 표시된다", states[hour] == states[hour + 1] == "approved")
        r.step("현황표에서 내 예약으로 표시된다", any(b["id"] == rid and b["mine"] for b in row["reservations"]))

        items = student.get("/api/notifications")["items"]
        note = next((n for n in items if n["type"] == "reservation_approved" and n["data"].get("reservation_id") == rid), None)
        r.step("승인 알림이 도착한다(링크 /room)", note is not None and note["link"] == "/room")
        r.step("알림을 읽음 처리할 수 있다", student.post(f"/api/notifications/{note['id']}/read")["read"] is True)
        r.step("승인 후 이용수칙을 계속 볼 수 있다", bool(student.get("/api/rooms/rules")["usage_rules"]))
    finally:
        cancelled = student.post(f"/api/reservations/{rid}/cancel")
    r.step("(정리) 취소하면 canceled다", cancelled["status"] == "canceled")
    again = student.get(f"/api/rooms/availability?date={day.isoformat()}")
    row = next(x for x in again["rooms"] if x["room"]["id"] == room["id"])
    r.step("(정리) 현황표가 다시 '빔'이 된다", {h["hour"]: h["state"] for h in row["hours"]}[hour] == "free")


# ── 시나리오 2: 면담 ────────────────────────────────────────────────
def scenario_meeting(student: Api, staff: Api, r: Report) -> None:
    types = student.get("/api/meetings/types")
    r.step("면담 유형 6종이 있다", len(types) == 6, ", ".join(t["name"] for t in types))
    freeze = next(t for t in types if t["code"] == "freeze")

    first, last = weekdays_from(1, 1)[0], weekdays_from(1, 6)[-1]
    slots = student.get(f"/api/meetings/slots?from={first.isoformat()}&to={last.isoformat()}")
    open_slots = [s for s in slots if s["available"]]
    r.step("신청 가능한 시간이 있다(시연 데이터 필요: manage.py seed_demo)", bool(open_slots), f"{len(open_slots)}개")
    slot = open_slots[0]

    created = student.post(
        "/api/meetings",
        {"type_id": freeze["id"], "slot_at": slot["start_at"], "content": "E2E 시연 점검", "notify_slack": False},
    )
    mid = created["id"]
    try:
        r.step("신청하면 '배정 중'(pending)이다", created["status"] == "pending")
        mine = {x["id"]: x for x in student.get("/api/meetings/me")}
        r.step("내 신청 내역에 보인다", mine.get(mid, {}).get("status") == "pending")

        pending = {x["id"]: x for x in staff.get("/api/staff/meetings?status=pending")}
        r.step("운영팀 목록에 교육생 정보와 함께 보인다", pending.get(mid, {}).get("student", {}).get("intra_id") == "student")

        members = staff.get("/api/staff/members")
        r.step("담당자로 지정할 운영팀 목록이 있다", bool(members))
        assigned = staff.call("PATCH", f"/api/staff/meetings/{mid}/assign", {"staff_id": members[0]["id"]})
        r.step("담당자를 배정할 수 있다", assigned["staff"]["id"] == members[0]["id"])

        confirmed = staff.post(f"/api/staff/meetings/{mid}/confirm", {"location": "1층 사무실 앞"})
        r.step("장소를 넣어 확정하면 confirmed다", confirmed["status"] == "confirmed" and confirmed["location"] == "1층 사무실 앞")

        mine = {x["id"]: x for x in student.get("/api/meetings/me")}
        r.step("교육생 화면에 확정 일시·담당·장소가 보인다", mine[mid]["status"] == "confirmed" and mine[mid]["staff"] and mine[mid]["location"])
        slots_after = student.get(f"/api/meetings/slots?from={first.isoformat()}&to={last.isoformat()}")
        same = next(s for s in slots_after if s["start_at"] == slot["start_at"])
        r.step("확정된 시간은 마감으로 바뀐다", same["remaining"] == slot["remaining"] - 1)

        items = student.get("/api/notifications")["items"]
        note = next((n for n in items if n["type"] == "meeting_confirmed" and n["data"].get("meeting_id") == mid), None)
        r.step("확정 알림이 도착한다(링크 /meeting)", note is not None and note["link"] == "/meeting")
        student.post(f"/api/notifications/{note['id']}/read")
    finally:
        cancelled = student.post(f"/api/meetings/{mid}/cancel")
    r.step("(정리) 취소하면 canceled다", cancelled["status"] == "canceled")
    restored = student.get(f"/api/meetings/slots?from={first.isoformat()}&to={last.isoformat()}")
    back = next(s for s in restored if s["start_at"] == slot["start_at"])
    r.step("(정리) 시간이 다시 열린다", back["remaining"] == slot["remaining"])


def run_once(base: str, number: int, check_spa: bool = True) -> tuple[bool, list[str]]:
    report = Report()
    started = time.time()
    try:
        plain = Api(base, "web")
        health = plain.get("/api/health")
        report.step("스택이 응답한다(/api/health)", health == {"status": "ok"})
        if check_spa:
            page = plain.page("/login")
            report.step("로그인 화면(SPA)이 열린다", "<div id=\"root\"" in page)

        student, staff = Api(base, "교육생"), Api(base, "운영팀")
        student.login("student")
        staff.login("staff")
        me = student.get("/api/auth/me")
        report.step("교육생으로 로그인한다", me["role"] == "student" and me["intra_id"] == "student")
        report.step("운영팀으로 로그인한다", staff.get("/api/auth/me")["role"] == "staff")
        report.step("교육생은 운영 API가 막힌다(403)", student.call("GET", "/api/staff/meetings", expect=(403,)) is not None)

        report.lines.append("  [시나리오 1] 회의실 예약 → 승인 → 결과 확인")
        scenario_room(student, staff, report)
        report.lines.append("  [시나리오 2] 면담 신청 → 배정·확정 → 결과 확인")
        scenario_meeting(student, staff, report)
    except StepFailed as exc:
        report.lines.append(f"    ✗ 실패: {exc}")
        return False, report.lines + [f"  결과: 실패 ({time.time() - started:.1f}초)"]
    return True, report.lines + [f"  결과: 통과 ({time.time() - started:.1f}초)"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", default="http://localhost:5173", help="접속 주소(기본 프론트 개발 서버)")
    parser.add_argument("--runs", type=int, default=1, help="처음부터 끝까지 반복할 횟수")
    parser.add_argument(
        "--skip-spa", action="store_true", help="화면(SPA) 확인을 건너뜀(백엔드 주소로 직접 점검할 때)"
    )
    args = parser.parse_args(argv)

    failures = 0
    for number in range(1, args.runs + 1):
        print(f"[{number}/{args.runs}회차] {args.base}")
        ok, lines = run_once(args.base, number, check_spa=not args.skip_spa)
        print("\n".join(lines))
        failures += 0 if ok else 1
    print(f"\n요약: {args.runs}회 중 {args.runs - failures}회 통과" + ("" if not failures else f", {failures}회 실패"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
