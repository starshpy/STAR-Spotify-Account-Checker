import os
import re
import sys
from typing import Any

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

RESET = "\033[0m"
BOLD = "\033[1m"


def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def gradient(text, c1=(16, 185, 129), c2=(110, 231, 183)):
    if not text:
        return text
    n = max(len(text) - 1, 1)
    out = []
    for i, ch in enumerate(text):
        t = i / n
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        out.append(f"{rgb(r, g, b)}{ch}")
    return "".join(out) + RESET


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def dig(obj: Any, *keys: str) -> Any:
    keyset = {k.lower() for k in keys}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in keyset and v not in (None, ""):
                return v
            found = dig(v, *keys)
            if found not in (None, ""):
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = dig(item, *keys)
            if found not in (None, ""):
                return found
    return None


def extract_first(text: str, patterns: list[str]):
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def infer_plan_key(name: str) -> str:
    if not name:
        return "unknown"
    n = name.strip().lower()
    if "free" in n:
        return "free"
    if "family" in n and "basic" in n:
        return "family_basic"
    if "family" in n:
        return "family_premium_v2"
    if "duo" in n:
        return "duo_premium"
    if "student" in n and "hulu" in n:
        return "student_premium_hulu"
    if "student" in n:
        return "student_premium"
    if "mini" in n:
        return "premium_mini"
    if "basic" in n and "premium" in n:
        return "basic_premium"
    if "premium" in n:
        return "premium"
    return "unknown"


def plan_label(key: str, raw: str | None) -> str:
    mapping = {
        "premium": "Premium",
        "premium_mini": "Premium Mini",
        "basic_premium": "Premium Basic",
        "student_premium": "Student Premium",
        "student_premium_hulu": "Student Premium (Hulu)",
        "duo_premium": "Duo Premium",
        "family_premium_v2": "Premium Family",
        "family_basic": "Family Basic",
        "free": "Free",
    }
    if key in mapping:
        return mapping[key]
    if raw and raw.strip():
        return raw.strip()
    return "Unknown"


def make_session(sp_dc: str) -> requests.Session:
    s = requests.Session()
    s.cookies.set("sp_dc", sp_dc.strip(), domain=".spotify.com", path="/")
    s.headers.update(
        {
            "User-Agent": UA,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "identity",
        }
    )
    return s


def get_plan(session: requests.Session) -> tuple[str, str | None]:
    headers = {"Referer": "https://www.spotify.com/account/overview/"}
    urls = [
        "https://www.spotify.com/api/account/v2/plan/",
        "https://www.spotify.com/jp/api/account/v2/plan/",
        "https://www.spotify.com/us/api/account/v2/plan/",
        "https://www.spotify.com/kr/api/account/v2/plan/",
        "https://www.spotify.com/ca-en/api/account/v2/plan/",
    ]
    for url in urls:
        try:
            r = session.get(url, headers=headers, timeout=20)
            if r.status_code != 200:
                continue
            data = r.json()
            if not isinstance(data, dict):
                continue
            raw = None
            if isinstance(data.get("plan"), dict):
                raw = data["plan"].get("name") or data["plan"].get("planName")
            if not raw:
                raw = dig(data, "name", "planName", "plan_name", "title", "label", "product")
            if not raw and isinstance(data.get("plan"), str):
                raw = data["plan"]
            key = infer_plan_key(str(raw or ""))
            if key != "unknown" or raw:
                return key, str(raw) if raw else None
        except Exception:
            continue
    return "unknown", None


def get_plan_from_overview(session: requests.Session) -> tuple[str, str | None]:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "User-Agent": UA,
    }
    for url in [
        "https://www.spotify.com/account/overview/",
        "https://www.spotify.com/jp/account/overview/",
        "https://www.spotify.com/us/account/overview/",
        "https://www.spotify.com/kr/account/overview/",
    ]:
        try:
            r = session.get(url, headers=headers, timeout=20)
            if r.status_code != 200:
                continue
            html = r.text.replace('\\"', '"').replace("&quot;", '"')
            raw = extract_first(
                html,
                [
                    r'"planName"\s*:\s*"([^"]+)"',
                    r'planName\\":\\"([^"]+)',
                    r'"currentPlan"\s*:\s*"([^"]+)"',
                ],
            )
            if raw:
                return infer_plan_key(raw), raw
        except Exception:
            continue
    return "unknown", None


def get_profile(session: requests.Session) -> dict:
    r = session.get(
        "https://www.spotify.com/api/account-settings/v1/profile",
        headers={"Referer": "https://www.spotify.com/account/profile/"},
        timeout=20,
        allow_redirects=False,
    )
    if r.status_code == 200:
        try:
            return r.json()
        except Exception:
            pass
    return {}


def get_family(session: requests.Session) -> dict:
    r = session.get(
        "https://www.spotify.com/api/family/v1/family/home",
        headers={"Referer": "https://www.spotify.com/account/family/"},
        timeout=20,
        allow_redirects=False,
    )
    if r.status_code == 200:
        try:
            return r.json()
        except Exception:
            pass
    return {}


def collect(sp_dc: str) -> dict:
    session = make_session(sp_dc)

    plan_key, plan_raw = get_plan(session)
    if plan_key == "unknown":
        plan_key, plan_raw = get_plan_from_overview(session)

    family = get_family(session)
    if plan_key in ("unknown", "free") and family:
        features = family.get("features") or []
        if isinstance(features, list) and features:
            plan_key = "family_premium_v2"
            plan_raw = plan_raw or "Premium Family"
        elif family.get("members") or family.get("maxCapacity"):
            plan_key = "family_premium_v2"
            plan_raw = plan_raw or "Premium Family"

    profile_json = get_profile(session)
    profile = (
        profile_json.get("profile")
        if isinstance(profile_json.get("profile"), dict)
        else profile_json
    )
    if not isinstance(profile, dict):
        profile = {}

    email = profile.get("email") or dig(profile_json, "email") or "—"
    country = profile.get("country") or dig(profile_json, "country") or "—"
    if country != "—":
        country = str(country).upper()
    username = profile.get("username") or dig(profile_json, "username") or "—"
    birthdate = (
        profile.get("birthdate")
        or profile.get("birthDate")
        or dig(profile_json, "birthdate")
        or "—"
    )

    return {
        "요금제": plan_label(plan_key, plan_raw),
        "이메일": email,
        "국가": country,
        "유저네임": username,
        "생년월일": birthdate,
    }


def print_banner():
    art = r"""   ______________    ____
  / ___/_  __/   |  / __ \
  \__ \ / / / /| | / /_/ /
 ___/ // / / ___ |/ _, _/
/____//_/ /_/  |_/_/ |_|"""
    for line in art.splitlines():
        print(BOLD + gradient(line) + RESET)
    print(gradient("=" * 50))
    print(BOLD + gradient("STAR Spotify Account Checker") + RESET)
    print(gradient("Produced by: star._.0412"))
    print(gradient("=" * 50))


def main():
    if sys.platform == "win32":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass

    clear_screen()
    print_banner()

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        sp_dc = args[0].strip()
    else:
        sp_dc = input(gradient("sp_dc") + " : ").strip()

    if not sp_dc:
        print(gradient("쿠키 없음", (239, 68, 68), (252, 165, 165)))
        input(gradient("엔터를 눌러 종료..."))
        return

    print(gradient("조회 중..."))
    print()

    try:
        info = collect(sp_dc)
    except Exception as e:
        print(gradient(f"오류 : {e}", (239, 68, 68), (252, 165, 165)))
        input(gradient("엔터를 눌러 종료..."))
        return

    for k, v in info.items():
        print(gradient(f"{k} : {v}"))
    print()
    input(gradient("엔터를 눌러 종료..."))


if __name__ == "__main__":
    main()