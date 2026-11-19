# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
# 블서로그 AI 도트 환경 2단계: FLUX 3 Image Klein 모델 받기 → E:\AI\ComfyUI_windows_portable\ComfyUI\models
# Hugging Face 공식 저장소 black-forest-labs/flux-3-image-klein-comfy (동의 필요). 토큰은 E:\AI\hf-home 에만 저장돼요 (C 아님)
import os
import shutil
import sys
import time

os.environ["HF_HOME"] = r"E:\AI\hf-home"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log-2.txt")
REPO = "black-forest-labs/flux-3-image-klein-comfy"
MODELS = r"E:\AI\ComfyUI_windows_portable\ComfyUI\models"
FILES = [  # 작은 것부터 (동의 확인 겸)
    "vae/flux2-vae.safetensors",
    "text_encoders/qwen3vl_4b_int8_convrot.safetensors",
    "diffusion_models/flux3-image-klein-int8-convrot.safetensors",
    "diffusion_models/flux3-image-klein-base-int8-convrot.safetensors",
    "text_encoders/qwen3.5_9b_flux3_prompt_upsampler_int8_convrot.safetensors",
]


def say(t):
    print(t, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(t + "\n")


def main():
    open(LOG, "w", encoding="utf-8").write("시작 " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
    if not os.path.isdir(MODELS):
        say("!! ComfyUI 가 아직 없어요. 1-comfyui.bat 먼저")
        return False
    import getpass

    import huggingface_hub
    from huggingface_hub import get_token, hf_hub_download, login

    try:  # huggingface_hub 2.x
        from huggingface_hub.errors import GatedRepoError, HfHubHTTPError
    except ImportError:
        from huggingface_hub.utils import GatedRepoError, HfHubHTTPError

    say("huggingface_hub " + huggingface_hub.__version__)
    say("E 남은 공간: %.1f GB" % (shutil.disk_usage("E:\\").free / 1e9))
    if not get_token():
        say("")
        say("Hugging Face 토큰(Read)을 붙여 넣고 Enter 를 눌러 주세요.")
        say("  화면에 글자가 안 보이는 게 정상이에요. 붙여넣기는 마우스 오른쪽 클릭 또는 Ctrl+V")
        tok = getpass.getpass("토큰: ").strip()
        if not tok.startswith("hf_"):
            say("!! hf_ 로 시작하는 토큰이 아니에요. 다시 실행해 주세요")
            return False
        try:
            login(token=tok)
        except Exception as e:  # 버전마다 login 이 달라서: 안 되면 토큰 파일에 직접
            say("  (login 대신 토큰 파일에 저장: %r)" % (type(e).__name__,))
            os.makedirs(os.environ["HF_HOME"], exist_ok=True)
            with open(os.path.join(os.environ["HF_HOME"], "token"), "w", encoding="utf-8") as f:
                f.write(tok)
        del tok
        if not get_token():
            say("!! 토큰 저장이 안 됐어요")
            return False
        say("  토큰 저장됨 (E:\\AI\\hf-home)")
    for f in FILES:
        for attempt in range(1, 4):
            try:
                say("받는 중: " + f)
                p = hf_hub_download(REPO, f, local_dir=MODELS)
                say("  끝 %.2f GB → %s" % (os.path.getsize(p) / 1e9, p))
                break
            except GatedRepoError:
                say("!! 동의가 안 돼 있어요: https://huggingface.co/" + REPO + " 에서 로그인 → 조건 동의 후 다시 실행")
                return False
            except HfHubHTTPError as e:
                say("!! 받기 오류 (%d번째): %s" % (attempt, str(e).splitlines()[0]))
                if "401" in str(e):
                    say("   토큰이 틀렸어요. 다시 실행하면 새로 물어봐요")
                    try:
                        huggingface_hub.logout()
                    except Exception:
                        os.remove(os.path.join(os.environ["HF_HOME"], "token"))
                    return False
                time.sleep(5)
            except Exception as e:
                say("!! 오류 (%d번째): %r" % (attempt, e))
                time.sleep(5)
        else:
            return False
    say("E 남은 공간: %.1f GB" % (shutil.disk_usage("E:\\").free / 1e9))
    return True


if __name__ == "__main__":
    ok = main()
    say("DONE" if ok else "FAILED")
    sys.exit(0 if ok else 1)
