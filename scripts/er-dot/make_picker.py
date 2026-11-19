# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
도트 후보 고르기 페이지 만들기 (claude.ai 아티팩트로 올려요, 11-20)

review_batch.py 가 만든 폴더(dot/<ER>_<이름>/<자세>.png + report.json)와 ai-prompts.json 을 읽어서
  <나올 폴더>/index.html   고르기 페이지 (SG가 실험체마다 앞 · 뒤 하나씩 누르면 db 의 picks/<이름> 에 저장)
  <나올 폴더>/front.png    앞모습 도트 모음 (가로 5칸 = fa~fe, 세로 = 실험체 순서, 칸 80×80)
  <나올 폴더>/back.png     뒷모습 도트 모음 (칸 80×120)
  <나올 폴더>/roster.json  실험체 순서 · 이름 · 검사 결과
를 만들어요. 올릴 때 Artifact 의 files 로 front.png · back.png · roster.json 을 같이 올리고 capabilities {db: {}}.

  python3 scripts/er-dot/make_picker.py <review 폴더> <나올 폴더>
고른 결과는 ArtifactData 로 picks 컬렉션을 읽어요: {front: "fc", back: "bd", redoFront: false, redoBack: false}
"""
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
FRONT_POSES = ["fa", "fb", "fc", "fd", "fe"]
BACK_POSES = ["ba", "bb", "bc", "bd", "be"]


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    review, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    prompts = json.loads((HERE / "ai-prompts.json").read_text(encoding="utf-8"))
    report = json.loads((review / "report.json").read_text(encoding="utf-8"))
    chars = sorted(prompts["characters"].items(), key=lambda kv: kv[1]["er"])
    front = Image.new("RGBA", (80 * 5, 80 * len(chars)), (0, 0, 0, 0))
    back = Image.new("RGBA", (80 * 5, 120 * len(chars)), (0, 0, 0, 0))
    roster = []
    for row, (slug, c) in enumerate(chars):
        key = f"{c['er']:03d}_{slug}"
        flags = report.get(key, {})
        have = {}
        for col, pose in enumerate(FRONT_POSES + BACK_POSES):
            p = review / "dot" / key / f"{pose}.png"
            if not p.exists():
                continue
            im = Image.open(p).convert("RGBA")
            if pose[0] == "f":
                front.alpha_composite(im, (80 * col, 80 * row))
            else:
                back.alpha_composite(im, (80 * (col - 5), 120 * row))
            have[pose] = flags.get(pose, [])
        roster.append({"slug": slug, "er": c["er"], "name": c["name"], "poses": have})
    front.save(out / "front.png", optimize=True)
    back.save(out / "back.png", optimize=True)
    (out / "roster.json").write_text(json.dumps(roster, ensure_ascii=False), encoding="utf-8")
    html = (HERE / "picker.html").read_text(encoding="utf-8")
    (out / "index.html").write_text(html, encoding="utf-8")
    n = sum(len(r["poses"]) for r in roster)
    print(f"{len(roster)}명 · 도트 {n}장 → {out}")


if __name__ == "__main__":
    main()
