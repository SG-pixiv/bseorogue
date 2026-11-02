<!--
SPDX-FileCopyrightText: 2026 SG
SPDX-License-Identifier: AGPL-3.0-only
-->

# 블서로그 (bseorogue)

이터널 리턴 실험체로 즐기는 로그라이트 웹게임이에요. 큐 잡는 동안 한 판씩!
[무명섬](https://mumeiisland.vercel.app)에서 랭킹을 볼 수 있어요.

- 기획과 정해진 규칙: [docs/기획.md](docs/기획.md)
- 원본에서 바꾼 것: [docs/원본에서-바꾼-것.md](docs/원본에서-바꾼-것.md)

## 바탕이 된 코드
이 게임은 [포켓로그(PokeRogue)](https://github.com/pagefaultgames/pokerogue) v1.12.2.3
(커밋 `7c0881255af5cd51992e513ff93c2f71adbe40e0`, 2026-10-30)을 바탕으로 2026-11-02부터 고친 버전이에요.
포켓로그 코드는 Pagefault Games의 저작물이고 **AGPL-3.0-only** 라이선스를 따라요.
그래서 블서로그 코드도 AGPL-3.0-only로 공개해요. 게임을 웹에서 쓰는 누구나 이 저장소에서 전체 소스를 받을 수 있어요.

포켓몬 그림 · 음악은 이 저장소에 없고, 쓰지 않아요 (포켓로그 그림 · 음악 저장소는 가져오지 않았어요).
한국어 글자는 포켓로그 번역 저장소(AGPL-3.0)의 한국어를 바탕으로 고쳐 쓰고 있어요.
포켓몬 이름 · 기술 이름은 이터널 리턴 실험체 · 스킬로 바꿔 나가는 중이고, 공개 전에 전부 바꿔요.

## 이터널 리턴 리소스
이터널 리턴의 실험체 · 일러스트 · 아이콘 · 폰트 · 사운드는 님블뉴런(Nimble Neuron)의 저작물이에요.
님블뉴런 IP 이용 정책에 따라 비상업 2차 창작으로 쓰고, `assets/er/` 아래에 따로 둬요.
이 리소스에는 AGPL이 적용되지 않아요 (`LICENSES/LicenseRef-NimbleNeuron.txt`).
블서로그는 님블뉴런의 공식 게임이 아니에요.

## 개발
Node.js 24 이상과 pnpm 10이 필요해요.

```bash
pnpm install
pnpm start:dev     # http://localhost:8000
pnpm test
pnpm build         # dist/ 에 배포용 파일
```

### 임시 그림
지금 `assets/` 의 그림 · 소리는 `scripts/placeholder-assets/make.py` 가 만든 단색 임시 그림 · 무음이에요.
포켓로그 그림 저장소에서 파일 이름 · 크기 · 칸 위치만 읽어서 새로 그렸고, 원본 그림은 들어 있지 않아요.
진짜 그림(이터널 리턴 리소스 · SG 그림)을 같은 이름으로 넣으면 그대로 바뀌어요. 다시 만들어도 진짜 그림은 덮어쓰지 않아요.

### 블서로그 규칙
파티 인원 · 클래식 길이 · 싱글 배틀 같은 규칙은 `src/bseorogue.ts` 한곳에 있어요.

### 이터널 리턴 데이터 받기
`scripts/er-data/fetch.mjs` 가 ER 공식 API에서 실험체 스탯 · 아이템 · 이름을 받아요.
키는 `er-key.txt` 에 적어 두고(깃허브에 올리지 않아요) `node scripts/er-data/fetch.mjs` 로 실행해요.
받은 `er-data` 폴더로 `node scripts/er-data/build.mjs <er-data 폴더>` 를 실행하면 `src/data/bseorogue/er-data.ts` 가 새로 만들어져요.

### 무명섬 연결 (랭킹 · KEL 팀)
배포 환경 변수에 무명섬과 같은 `VITE_SUPABASE_URL` · `VITE_SUPABASE_ANON_KEY` (공개 키) 를 넣으면,
판이 끝날 때 닉네임을 적고 무명섬 랭킹에 올릴 수 있어요. 키가 없으면 랭킹 올리기만 건너뛰어요.

## 라이선스
- 코드: AGPL-3.0-only ([LICENSE](LICENSE))
- 원본 포켓로그 문서(`docs/pokerogue-*.md` 등): 각 파일에 적힌 라이선스(CC-BY-NC-SA-4.0 등)
- 이터널 리턴 리소스(`assets/er/`): 님블뉴런 저작물, AGPL 적용 안 됨
