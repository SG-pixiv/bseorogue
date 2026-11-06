/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 블서로그 마우스 조작: 화면마다 "누를 수 있는 곳" 목록
 *
 * 화면(UI 처리기)마다 MouseTarget 목록을 돌려주면, mouse-controller.ts 가
 * 마우스를 올렸을 때 hover(커서 옮기기), 눌렀을 때 click(결정)을 불러요.
 * 키보드 조작은 그대로예요. 마우스는 같은 처리기에 같은 버튼을 보내는 길을 하나 더 만든 거예요.
 */
import { globalScene } from "#app/global-scene";
import type { Button } from "#enums/buttons";
import Phaser from "phaser";

export interface MouseTarget {
  /** 검사 · 브라우저 확인용 이름 (한 화면 안에서 겹치지 않게) */
  label: string;
  /** 화면(게임 1920×1080) 좌표의 누르는 곳. 지금 안 보이면 null */
  rect: () => Phaser.Geom.Rectangle | null;
  /** 마우스를 올렸을 때 (보통 커서를 그 칸으로) */
  hover?: () => void;
  /** 마우스가 나갔을 때 (보통 없음) */
  leave?: () => void;
  /** 눌렀을 때 */
  click: () => void;
  /** 터치에서도 한 번 누르면 바로 (먼저 고르기 없이) */
  instant?: boolean;
}

type Shown = {
  visible: boolean;
  alpha?: number;
  parentContainer?: Phaser.GameObjects.Container | null;
  displayList?: unknown;
};

/** 자기와 감싼 컨테이너가 모두 보이고, 화면에 붙어 있는지 */
export function isShown(obj: Shown | null | undefined): boolean {
  let o: Shown | null | undefined = obj;
  while (o) {
    if (!o.visible || o.alpha === 0) {
      return false;
    }
    if (!o.parentContainer) {
      // 맨 바깥은 씬 화면 목록에 있어야 해요 (떼어 둔 오브젝트는 안 보여요)
      return !!o.displayList;
    }
    o = o.parentContainer;
  }
  return false;
}

/** 여러 오브젝트를 감싸는 사각형 (보이는 것만) */
export function unionRect(
  ...objs: ((Shown & { getBounds: () => Phaser.Geom.Rectangle }) | null | undefined)[]
): () => Phaser.Geom.Rectangle | null {
  return () => {
    let out: Phaser.Geom.Rectangle | null = null;
    for (const o of objs) {
      const r = objRect(o)();
      if (r) {
        out = out ? Phaser.Geom.Rectangle.Union(out, r, out) : r;
      }
    }
    return out;
  };
}

/** 게임 오브젝트가 화면에서 차지하는 곳 (pad 만큼 넓혀서) */
export function objRect(
  obj: (Shown & { getBounds: (out?: Phaser.Geom.Rectangle) => Phaser.Geom.Rectangle }) | null | undefined,
  pad = 0,
): () => Phaser.Geom.Rectangle | null {
  return () => {
    if (!obj || !isShown(obj)) {
      return null;
    }
    const r = obj.getBounds();
    if (r.width <= 0 || r.height <= 0) {
      return null;
    }
    if (pad) {
      r.setTo(r.x - pad * 6, r.y - pad * 6, r.width + pad * 12, r.height + pad * 12);
    }
    return r;
  };
}

/**
 * 컨테이너에서 지금 보이는 자식만 감싸는 사각형 (pad 만큼 넓혀서).
 * 컨테이너 getBounds 는 숨은 자식까지 넣어서, 숨은 자식이 멀리 있으면 칸이 엉뚱하게 커져요
 * (예: 보상 고르기의 숨은 몬스터볼 그림이 화면 위쪽에 있어서 보상 칸이 상점 칸까지 덮었어요)
 */
export function shownChildrenRect(
  container: Phaser.GameObjects.Container | null | undefined,
  pad = 0,
): () => Phaser.Geom.Rectangle | null {
  return () => {
    if (!container || !isShown(container)) {
      return null;
    }
    const children = container.list.filter(c => typeof (c as { getBounds?: unknown }).getBounds === "function");
    const out = unionRect(...(children as unknown as Parameters<typeof unionRect>))();
    return out && pad ? out.setTo(out.x - pad * 6, out.y - pad * 6, out.width + pad * 12, out.height + pad * 12) : out;
  };
}

/** 컨테이너 안 좌표(x, y, w, h)를 화면 좌표로 */
export function localRect(
  parent: Phaser.GameObjects.Container | null | undefined,
  x: number,
  y: number,
  w: number,
  h: number,
): () => Phaser.Geom.Rectangle | null {
  return () => {
    if (!parent || !isShown(parent)) {
      return null;
    }
    const m = parent.getBoundsTransformMatrix();
    const a = m.transformPoint(x, y);
    const b = m.transformPoint(x + w, y + h);
    return new Phaser.Geom.Rectangle(Math.min(a.x, b.x), Math.min(a.y, b.y), Math.abs(b.x - a.x), Math.abs(b.y - a.y));
  };
}

/** 오브젝트 하나의 왼쪽 위를 기준으로 한 사각형 (그 오브젝트가 든 컨테이너 좌표로) */
export function relRect(
  obj:
    | (Shown & { x: number; y: number; displayWidth: number; displayHeight: number; originX: number; originY: number })
    | null
    | undefined,
  x: number,
  y: number,
  w: number,
  h: number,
): () => Phaser.Geom.Rectangle | null {
  return () => {
    if (!obj || !isShown(obj) || !obj.parentContainer) {
      return null;
    }
    const left = obj.x - obj.displayWidth * obj.originX;
    const top = obj.y - obj.displayHeight * obj.originY;
    return localRect(obj.parentContainer, left + x, top + y, w, h)();
  };
}

/** 지금 화면의 처리기에 버튼 보내기 (키보드로 누른 것과 같아요) */
export function press(button: Button): boolean {
  return globalScene.ui.processInput(button);
}

/** 처리기 안쪽 값 읽기 (원래 코드는 그대로 두려고 바깥에서 들여다봐요) */
export function peek<T>(handler: unknown): T {
  return handler as T;
}
