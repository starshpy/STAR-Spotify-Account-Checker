# STAR Spotify Account Checker

`sp_dc` 쿠키로 Spotify 계정 정보와 요금제를 조회하는 Python 도구입니다.

Produced by: star._.0412

![preview](https://github.com/starshpy/STAR-Spotify-Account-Checker/blob/1466fc45e63c6a6a833080bbb74c5d47ccc010d0/pixelated.jpg)

---

## 기능

- 요금제 조회 (Free, Premium, Family, Duo 등)
- 이메일, 국가, 유저네임, 생년월일 출력
- 터미널 초록 그라데이션 UI

---

## 요구 사항

- Python 3.10 이상
- requests

```bash
pip install requests
```

---

## 사용 방법

### 1. sp_dc 쿠키 복사

1. 브라우저에서 https://open.spotify.com 접속 후 로그인
2. F12 (개발자 도구) 열기
3. Application (또는 저장소) 탭 선택
4. Cookies → `https://open.spotify.com`
5. `sp_dc` 값을 복사

### 2. 실행

```bash
python main.py
```

실행 후 `sp_dc` 값을 붙여넣고 Enter를 누릅니다.

조회가 끝나면 엔터를 눌러 종료합니다.

---

## 출력 예시

```
   ______________    ____
  / ___/_  __/   |  / __ \
  \__ \ / / / /| | / /_/ /
 ___/ // / / ___ |/ _, _/
/____//_/ /_/  |_/_/ |_|
==================================================
STAR Spotify Account Checker
Produced by: star._.0412
==================================================
sp_dc : ...

요금제 : Premium Family
이메일 : 
