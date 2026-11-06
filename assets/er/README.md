# 이터널 리턴 리소스 (님블뉴런 저작물)

이 폴더의 그림 · 소리는 님블뉴런(Nimble Neuron)의 이터널 리턴 팬키트에서 가져와 크기만 줄인 것이에요.
블서로그 코드의 AGPL-3.0 이 적용되지 않아요. 다시 쓰려면 님블뉴런 IP 이용 정책을 직접 확인해 주세요.
https://support.playeternalreturn.com/hc/ko/articles/63456926675865

- `char/<ER번호>_<스킨번호>.png` 전투 그림 (팬키트 전신, 없으면 반신)
- `char-icons.png` 아이콘 한 장 (팬키트 Mini 얼굴)
- `art-sources.json` 그림마다 어느 팬키트 파일 · 종류(전신 · 반신 · 얼굴)로 만들었는지
- `voice/<ER번호>_<q|w|e|r|select>.m4a` 스킬 · 등장 대사 음성 (팬키트 Voice Line, 한국어 > 영어 > 일본어 중 하나, AAC 모노 64kbps)
- `voice-sources.json` 실험체마다 음성 언어 · zip · 고른 파일

다시 만들기 (팬키트가 zip 여러 개로 나뉘어 있어서 기본은 더하기예요. 처음부터는 `--fresh`):
- 그림: `python3 scripts/fankit/build_art.py <팬키트 폴더> [<폴더> …]`
- 음성: `python3 scripts/fankit/build_voice.py <팬키트 폴더> [<폴더> …]` (ffmpeg 필요)
