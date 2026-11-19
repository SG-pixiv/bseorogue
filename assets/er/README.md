# 이터널 리턴 리소스 (님블뉴런 저작물)

이 폴더의 그림 · 소리는 님블뉴런(Nimble Neuron)의 이터널 리턴 팬키트 · 게임에서 가져와 크기만 줄인 것이에요.
블서로그 코드의 AGPL-3.0 이 적용되지 않아요. 다시 쓰려면 님블뉴런 IP 이용 정책을 직접 확인해 주세요.
https://support.playeternalreturn.com/hc/ko/articles/63456926675865

- `char/<ER번호>_<스킨번호>.png` 전투 그림 (팬키트 전신, 없으면 반신)
- `char-icons.png` 아이콘 한 장 (팬키트 Mini 얼굴)
- `art-sources.json` 그림마다 어느 팬키트 파일 · 종류(전신 · 반신 · 얼굴)로 만들었는지
- `voice/<ER번호>_<q|w|e|r|select|die>_<0|1|2>.m4a` 스킬 · 등장 · 쓰러질 때 대사 음성, 키마다 최대 3개 (팬키트 Voice Line, 한국어 > 영어 > 일본어 중 하나, AAC 모노 64kbps)
- `skill/<ER번호>_<p|q|w|e|r>.png` 스킬 아이콘 (팬키트 Skill Icon, 72×72 · 128색, p = 패시브)
- `skill-icon-sources.json` 아이콘마다 어느 팬키트 파일로 만들었는지
- `voice-sources.json` 실험체마다 음성 언어 · zip(또는 낱개 폴더) · 고른 파일
- `announce/<키>_<0|1>.m4a` 루미아 섬 안내 방송 (팬키트 `01. Announce/KOR` 한국어 57개, 같은 방송 2개씩 · AAC 모노 64kbps), `announce-sources.json` 키마다 어느 팬키트 파일 · 무슨 방송 · 블서로그에서 트는 곳
- `item/<아이템 파일 이름>.png` 아이템 도트 (팬키트 `02. Ingame_Image` 아이템 그림을 32×32 · 14색 · 외곽선 1px 도트로 줄인 것. 강화 모듈 · 테라피스 · 부적은 색만 바꿈), `item-sources.json` 아이템마다 어느 팬키트 파일로 만들었는지
- `audio/{ui,se,battle_anims}/<이름>.wav` · `audio/bgm/<이름>.mp3` 효과음 · BGM (이터널 리턴 게임 소리, 11-18 SG PC 설치 폴더에서 AnimeStudio 로 꺼냄. 32kHz 모노 · MP3 96kbps), `sfx/<ER번호>_<q|w|e|r>.m4a` 실험체 스킬 효과음 (AAC 모노 64kbps), `sound-sources.json` 자리마다 어느 게임 소리로 만들었는지
- `area-illust/<지역>_<day|night>.jpg` 지역 일러스트 (이터널 리턴 게임 스토리 모드 대화 배경 `Img_BG_Lumia_*`, 11-19 SG PC 설치 폴더 13.0.0 Addressables 에서 꺼내 절반 크기 1022×510), `area-illust-sources.json` 파일마다 어느 게임 그림인지 — **11-19 SG가 포켓로그 방식으로 정해서 전투 배경에는 안 써요** (지역 색 참고 · 나중에 지역 카드 · 로딩 그림용으로 남겨 둠)
- `dot/<ER번호>_<스킨>.png` · `dot/<ER번호>_<스킨>_icon.png` 실험체 도트 (블서로그용으로 새로 그린 것, 전투 80×80 · 아이콘 40×30 1배), `dot-icons.png` 도트 아이콘 한 장. 있으면 팬키트 그림보다 먼저 써요

다시 만들기 (팬키트가 zip 여러 개로 나뉘어 있어서 기본은 더하기예요. 처음부터는 `--fresh`):
- 그림: `python3 scripts/fankit/build_art.py <팬키트 폴더> [<폴더> …]`
- 스킬 아이콘: `python3 -B scripts/fankit/build_skill_icons.py <팬키트 폴더> [<폴더> …]`
- 음성: `python3 scripts/fankit/build_voice.py <팬키트 폴더> [<폴더> …]` (ffmpeg 필요)
- 안내 방송: `python3 -I -B scripts/fankit/build_announce.py <팬키트 폴더>` (안에 `01. Announce/KOR` 가 있는 폴더, ffmpeg 필요)
- 아이템 도트: `python3 -I -B scripts/fankit/build_item_dots.py <팬키트 폴더>` → `python3 -I -B scripts/er-ui/make_items.py` (아틀라스 다시)
- 소리: `python3 -I -B scripts/sound/build_er_sound.py <꺼낸 폴더>` (UnityPy · ffmpeg 필요, 꺼내는 법은 스크립트 맨 위)
- 지역 일러스트: `python3 -I -B scripts/er-ui/build_area_illust.py <묶음 또는 PNG 폴더>` (전투 배경은 `scripts/er-ui/make_arenas.py` 가 코드로 따로 그려요)
- 도트: `python3 -B scripts/er-dot/import_dot.py <도트.png 또는 폴더>` (규격 검사 후 넣기, 검사만은 `--check`)
