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

포켓몬 그림 · 음악 · 이름 · 번역문은 이 저장소에 없고, 쓰지 않아요.
(포켓로그의 그림 · 음악 저장소와 번역 저장소는 가져오지 않았어요.)

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

### 이터널 리턴 데이터 받기
`scripts/er-data/fetch.mjs` 가 ER 공식 API에서 실험체 스탯 · 아이템 · 이름을 받아요.
키는 `er-key.txt` 에 적어 두고(깃허브에 올리지 않아요) `node scripts/er-data/fetch.mjs` 로 실행해요.

## 라이선스
- 코드: AGPL-3.0-only ([LICENSE](LICENSE))
- 원본 포켓로그 문서(`docs/pokerogue-*.md` 등): 각 파일에 적힌 라이선스(CC-BY-NC-SA-4.0 등)
- 이터널 리턴 리소스(`assets/er/`): 님블뉴런 저작물, AGPL 적용 안 됨
