import argparse
import csv
import glob
import math
import os
import re
import statistics
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image, ImageDraw

from backend.image_steg import ImageSteganography


@dataclass
class SampleResult:
    sample_id: str
    cover_path: str
    secret_path: str
    stego_path: str
    revealed_path: str
    psnr_cover_stego: float
    psnr_secret_revealed: float
    ssim_secret_revealed: float


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def read_img_rgb(path: str, size: Tuple[int, int] = (256, 256)) -> np.ndarray:
    img = Image.open(path).convert("RGB").resize(size)
    return np.array(img)


def save_img_rgb(path: str, arr: np.ndarray) -> None:
    Image.fromarray(arr.astype(np.uint8)).save(path)


def compute_psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    if mse <= 1e-12:
        return float("inf")
    return 20.0 * math.log10(255.0 / math.sqrt(mse))


def compute_ssim_channel(x: np.ndarray, y: np.ndarray) -> float:
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2

    x = x.astype(np.float64)
    y = y.astype(np.float64)

    mu_x = cv2.GaussianBlur(x, (11, 11), 1.5)
    mu_y = cv2.GaussianBlur(y, (11, 11), 1.5)

    mu_x2 = mu_x * mu_x
    mu_y2 = mu_y * mu_y
    mu_xy = mu_x * mu_y

    sigma_x2 = cv2.GaussianBlur(x * x, (11, 11), 1.5) - mu_x2
    sigma_y2 = cv2.GaussianBlur(y * y, (11, 11), 1.5) - mu_y2
    sigma_xy = cv2.GaussianBlur(x * y, (11, 11), 1.5) - mu_xy

    ssim_map = ((2 * mu_xy + c1) * (2 * sigma_xy + c2)) / ((mu_x2 + mu_y2 + c1) * (sigma_x2 + sigma_y2 + c2) + 1e-12)
    return float(ssim_map.mean())


def compute_ssim(a: np.ndarray, b: np.ndarray) -> float:
    channels = []
    for ch in range(3):
        channels.append(compute_ssim_channel(a[:, :, ch], b[:, :, ch]))
    return float(np.mean(channels))


def make_panel(cover: np.ndarray, stego: np.ndarray, secret: np.ndarray, revealed: np.ndarray, title: str, out_path: str) -> None:
    tile_w, tile_h = 256, 256
    header = 48
    panel = Image.new("RGB", (tile_w * 4, tile_h + header), (20, 20, 20))
    draw = ImageDraw.Draw(panel)

    labels = ["Cover", "Stego", "Secret", "Revealed"]
    imgs = [cover, stego, secret, revealed]

    for idx, arr in enumerate(imgs):
        panel.paste(Image.fromarray(arr), (idx * tile_w, header))
        draw.text((idx * tile_w + 8, 16), labels[idx], fill=(235, 235, 235))

    draw.text((8, 2), title, fill=(255, 210, 120))
    panel.save(out_path)


def collect_test_pairs(example_dir: str, n_pairs: int = 4) -> List[Tuple[str, str, str]]:
    candidates = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp", "*.JPEG", "*.JPG"):
        candidates.extend(glob.glob(os.path.join(example_dir, ext)))
    candidates = sorted(list(dict.fromkeys(candidates)))

    if len(candidates) < n_pairs * 2:
        raise RuntimeError(f"Need at least {n_pairs * 2} images in {example_dir}, found {len(candidates)}")

    pairs = []
    for i in range(n_pairs):
        cover = candidates[i]
        secret = candidates[i + n_pairs]
        pairs.append((f"sample_{i+1}", cover, secret))
    return pairs


def write_csv(path: str, rows: List[Dict], fieldnames: List[str]) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run_inference_on_pairs(steg: ImageSteganography, pairs: List[Tuple[str, str, str]], out_dir: str, password: str) -> List[SampleResult]:
    ensure_dir(out_dir)
    results: List[SampleResult] = []

    for sample_id, cover_path, secret_path in pairs:
        sample_dir = os.path.join(out_dir, sample_id)
        ensure_dir(sample_dir)

        stego_path = os.path.join(sample_dir, "stego.png")
        revealed_path = os.path.join(sample_dir, "revealed.png")
        grid_path = os.path.join(sample_dir, "grid_cover_stego_secret_revealed.png")

        steg.hide_image(cover_path, secret_path, stego_path, password=password)
        steg.reveal_image(stego_path, revealed_path, password=password)

        cover = read_img_rgb(cover_path)
        secret = read_img_rgb(secret_path)
        stego_img = read_img_rgb(stego_path)
        revealed = read_img_rgb(revealed_path)

        psnr_cs = compute_psnr(cover, stego_img)
        psnr_sr = compute_psnr(secret, revealed)
        ssim_sr = compute_ssim(secret, revealed)

        make_panel(cover, stego_img, secret, revealed, f"{sample_id} | password={password}", grid_path)

        results.append(
            SampleResult(
                sample_id=sample_id,
                cover_path=cover_path,
                secret_path=secret_path,
                stego_path=stego_path,
                revealed_path=revealed_path,
                psnr_cover_stego=psnr_cs,
                psnr_secret_revealed=psnr_sr,
                ssim_secret_revealed=ssim_sr,
            )
        )

    return results


def plot_sample_curves(results: List[SampleResult], out_path: str) -> None:
    sample_idx = list(range(1, len(results) + 1))
    psnr_cs = [r.psnr_cover_stego for r in results]
    psnr_sr = [r.psnr_secret_revealed for r in results]
    ssim_sr = [r.ssim_secret_revealed for r in results]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    axes[0].plot(sample_idx, psnr_cs, marker="o", label="PSNR Cover-Stego")
    axes[0].plot(sample_idx, psnr_sr, marker="o", label="PSNR Secret-Revealed")
    axes[0].set_xlabel("Sample")
    axes[0].set_ylabel("PSNR (dB)")
    axes[0].set_title("PSNR across 4 test samples")
    axes[0].grid(alpha=0.3)
    axes[0].legend()

    axes[1].plot(sample_idx, ssim_sr, marker="o", color="#2ca02c", label="SSIM Secret-Revealed")
    axes[1].set_xlabel("Sample")
    axes[1].set_ylabel("SSIM")
    axes[1].set_title("SSIM across 4 test samples")
    axes[1].set_ylim(0, 1)
    axes[1].grid(alpha=0.3)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=170)
    plt.close(fig)


def capture_feature_maps(steg: ImageSteganography, cover_path: str, secret_path: str, out_dir: str, password: str) -> None:
    ensure_dir(out_dir)

    activations: Dict[str, torch.Tensor] = {}

    conv_h = [m for m in steg.h_net.modules() if isinstance(m, torch.nn.Conv2d)]
    conv_r = [m for m in steg.r_net.modules() if isinstance(m, torch.nn.Conv2d)]

    selected = {
        "hnet_conv_1": conv_h[0] if len(conv_h) > 0 else None,
        "hnet_conv_mid": conv_h[len(conv_h) // 2] if len(conv_h) > 1 else None,
        "hnet_conv_last": conv_h[-1] if len(conv_h) > 2 else None,
        "rnet_conv_1": conv_r[0] if len(conv_r) > 0 else None,
        "rnet_conv_mid": conv_r[len(conv_r) // 2] if len(conv_r) > 1 else None,
        "rnet_conv_last": conv_r[-1] if len(conv_r) > 2 else None,
    }

    hooks = []
    for name, layer in selected.items():
        if layer is None:
            continue

        def _make_hook(key):
            def _hook(_module, _inputs, outputs):
                activations[key] = outputs.detach().cpu()
            return _hook

        hooks.append(layer.register_forward_hook(_make_hook(name)))

    cover_pil = Image.open(cover_path).convert("RGB")
    secret_pil = Image.open(secret_path).convert("RGB")
    cover_pil = steg._make_square(cover_pil)
    secret_pil = steg._make_square(secret_pil)

    if password:
        secret_pil = steg._shuffle_image(secret_pil, password)

    cover = steg.transform(cover_pil).unsqueeze(0).to(steg.device)
    secret = steg.transform(secret_pil).unsqueeze(0).to(steg.device)

    with torch.no_grad():
        container = steg.h_net(torch.cat([cover, secret], dim=1))
        _revealed = steg.r_net(container)

    for hook in hooks:
        hook.remove()

    for name, tensor in activations.items():
        save_feature_grid(tensor, os.path.join(out_dir, f"{name}.png"), title=name)


def save_feature_grid(tensor: torch.Tensor, out_path: str, title: str, max_channels: int = 16, cols: int = 4) -> None:
    if tensor.ndim != 4 or tensor.shape[0] == 0:
        return

    fmap = tensor[0]
    channels = min(max_channels, fmap.shape[0])
    rows = math.ceil(channels / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.2, rows * 2.2))
    axes = np.array(axes).reshape(rows, cols)

    for idx in range(rows * cols):
        ax = axes[idx // cols, idx % cols]
        ax.axis("off")
        if idx >= channels:
            continue
        img = fmap[idx].numpy()
        min_v, max_v = float(img.min()), float(img.max())
        if max_v - min_v > 1e-8:
            img = (img - min_v) / (max_v - min_v)
        else:
            img = np.zeros_like(img)
        ax.imshow(img, cmap="viridis")

    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=170)
    plt.close(fig)


def summarize_results(results: List[SampleResult]) -> Dict[str, float]:
    return {
        "psnr_cover_stego_mean": statistics.mean([r.psnr_cover_stego for r in results]),
        "psnr_secret_revealed_mean": statistics.mean([r.psnr_secret_revealed for r in results]),
        "ssim_secret_revealed_mean": statistics.mean([r.ssim_secret_revealed for r in results]),
    }


def run_ablation(steg: ImageSteganography, pairs: List[Tuple[str, str, str]], out_dir: str) -> List[Dict]:
    ensure_dir(out_dir)
    rows = []

    settings = [
        {"name": "A_no_password", "hide_password": None, "reveal_password": None},
        {"name": "B_password_correct", "hide_password": "eval_pass_2026", "reveal_password": "eval_pass_2026"},
        {"name": "C_password_wrong", "hide_password": "eval_pass_2026", "reveal_password": "wrong_pass_2026"},
    ]

    for setting in settings:
        psnr_cs_values = []
        psnr_sr_values = []
        ssim_values = []
        runtimes = []

        for sample_id, cover_path, secret_path in pairs:
            variant_dir = os.path.join(out_dir, setting["name"], sample_id)
            ensure_dir(variant_dir)
            stego_path = os.path.join(variant_dir, "stego.png")
            revealed_path = os.path.join(variant_dir, "revealed.png")

            t0 = time.perf_counter()
            steg.hide_image(cover_path, secret_path, stego_path, password=setting["hide_password"])
            steg.reveal_image(stego_path, revealed_path, password=setting["reveal_password"])
            runtime_ms = (time.perf_counter() - t0) * 1000.0
            runtimes.append(runtime_ms)

            cover = read_img_rgb(cover_path)
            secret = read_img_rgb(secret_path)
            stego_img = read_img_rgb(stego_path)
            revealed = read_img_rgb(revealed_path)

            psnr_cs_values.append(compute_psnr(cover, stego_img))
            psnr_sr_values.append(compute_psnr(secret, revealed))
            ssim_values.append(compute_ssim(secret, revealed))

        rows.append(
            {
                "setting": setting["name"],
                "mean_psnr_cover_stego": statistics.mean(psnr_cs_values),
                "mean_psnr_secret_revealed": statistics.mean(psnr_sr_values),
                "mean_ssim_secret_revealed": statistics.mean(ssim_values),
                "mean_runtime_ms": statistics.mean(runtimes),
            }
        )

    return rows


def write_ablation_markdown(rows: List[Dict], out_path: str) -> None:
    ensure_dir(os.path.dirname(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Ablation Study Table\n\n")
        f.write("| Setting | Mean PSNR(Cover,Stego) | Mean PSNR(Secret,Revealed) | Mean SSIM(Secret,Revealed) | Mean Runtime (ms) |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for row in rows:
            f.write(
                f"| {row['setting']} | {row['mean_psnr_cover_stego']:.4f} | {row['mean_psnr_secret_revealed']:.4f} | {row['mean_ssim_secret_revealed']:.4f} | {row['mean_runtime_ms']:.2f} |\n"
            )


def parse_training_logs_for_curves(root: str, out_dir: str) -> None:
    ensure_dir(out_dir)
    log_files = glob.glob(os.path.join(root, "**", "*_log.txt"), recursive=True)

    pattern = re.compile(
        r"validation\[(?P<epoch>\d+)\]\s+val_Hloss\s*=\s*(?P<hloss>[0-9.eE+-]+)\s*\t?\s*val_Rloss\s*=\s*(?P<rloss>[0-9.eE+-]+)\s*\t?\s*val_Sumloss\s*=\s*(?P<sumloss>[0-9.eE+-]+)",
        re.IGNORECASE,
    )

    rows = []
    for log in log_files:
        with open(log, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = pattern.search(line)
                if not m:
                    continue
                epoch = int(m.group("epoch"))
                hloss = float(m.group("hloss"))
                rloss = float(m.group("rloss"))
                psnr_h = 10.0 * math.log10(1.0 / hloss) if hloss > 0 else float("inf")
                psnr_r = 10.0 * math.log10(1.0 / rloss) if rloss > 0 else float("inf")
                rows.append(
                    {
                        "log_file": log,
                        "epoch": epoch,
                        "val_hloss": hloss,
                        "val_rloss": rloss,
                        "val_sumloss": float(m.group("sumloss")),
                        "psnr_cover_container": psnr_h,
                        "psnr_secret_revealed": psnr_r,
                    }
                )

    if not rows:
        note = os.path.join(out_dir, "training_logs_missing.txt")
        with open(note, "w", encoding="utf-8") as f:
            f.write("No training *_log.txt files with validation lines found.\n")
            f.write("Expected lines like: validation[epoch] val_Hloss=... val_Rloss=...\n")
        return

    rows = sorted(rows, key=lambda x: x["epoch"])
    csv_path = os.path.join(out_dir, "training_metrics_extracted.csv")
    write_csv(
        csv_path,
        rows,
        [
            "log_file",
            "epoch",
            "val_hloss",
            "val_rloss",
            "val_sumloss",
            "psnr_cover_container",
            "psnr_secret_revealed",
        ],
    )

    epochs = [r["epoch"] for r in rows]
    psnr_h = [r["psnr_cover_container"] for r in rows]
    psnr_r = [r["psnr_secret_revealed"] for r in rows]

    plt.figure(figsize=(8, 5))
    plt.plot(epochs, psnr_h, marker="o", label="PSNR Cover-Container (from Hloss)")
    plt.plot(epochs, psnr_r, marker="o", label="PSNR Secret-Revealed (from Rloss)")
    plt.xlabel("Epoch")
    plt.ylabel("PSNR (dB)")
    plt.title("Training PSNR Curves (extracted from logs)")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "training_psnr_curves.png"), dpi=170)
    plt.close()

    with open(os.path.join(out_dir, "training_ssim_curve_note.txt"), "w", encoding="utf-8") as f:
        f.write("SSIM not found in training logs.\n")
        f.write("Add SSIM logging during training to plot SSIM-vs-epoch curve.\n")


def write_security_analysis(base_results: List[SampleResult], ablation_rows: List[Dict], out_path: str) -> None:
    ensure_dir(os.path.dirname(out_path))

    row_by_setting = {r["setting"]: r for r in ablation_rows}
    correct = row_by_setting.get("B_password_correct")
    wrong = row_by_setting.get("C_password_wrong")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Security Analysis\n\n")
        f.write("## Empirical Findings (4 image pairs)\n")
        f.write(f"- Mean PSNR(Cover,Stego): {statistics.mean([x.psnr_cover_stego for x in base_results]):.4f} dB\n")
        f.write(f"- Mean PSNR(Secret,Revealed): {statistics.mean([x.psnr_secret_revealed for x in base_results]):.4f} dB\n")
        f.write(f"- Mean SSIM(Secret,Revealed): {statistics.mean([x.ssim_secret_revealed for x in base_results]):.4f}\n\n")

        if correct and wrong:
            delta_psnr = correct["mean_psnr_secret_revealed"] - wrong["mean_psnr_secret_revealed"]
            delta_ssim = correct["mean_ssim_secret_revealed"] - wrong["mean_ssim_secret_revealed"]
            f.write("## Password Robustness\n")
            f.write(f"- PSNR drop with wrong password: {delta_psnr:.4f} dB\n")
            f.write(f"- SSIM drop with wrong password: {delta_ssim:.4f}\n\n")

        f.write("## Attack Surface Notes\n")
        f.write("- Model inversion/extraction attacks remain possible if API access is uncontrolled.\n")
        f.write("- Text mode currently uses AES-ECB in backend/text_steg.py, which leaks pattern structure and is not semantically secure.\n")
        f.write("- Temporary and upload directories should be periodically cleaned to avoid data retention risk.\n")
        f.write("- Add rate limiting, authentication, and request size limits on API endpoints.\n\n")

        f.write("## Recommended Hardening\n")
        f.write("1. Replace AES-ECB with AES-GCM (authenticated encryption).\n")
        f.write("2. Use random nonces/IVs and store with ciphertext.\n")
        f.write("3. Add API auth + per-user quota + rate limiting.\n")
        f.write("4. Encrypt temporary files at rest or avoid disk persistence when possible.\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--example-dir", default="d:/Stegen/pytorch-Deep-Steganography/example_pics")
    parser.add_argument("--h-model", default="d:/Stegen/backend/checkpoints/netH.pth")
    parser.add_argument("--r-model", default="d:/Stegen/backend/checkpoints/netR.pth")
    parser.add_argument("--output-dir", default="d:/Stegen/analysis")
    parser.add_argument("--password", default="eval_pass_2026")
    args = parser.parse_args()

    ensure_dir(args.output_dir)
    infer_dir = os.path.join(args.output_dir, "inference")
    feature_dir = os.path.join(args.output_dir, "feature_maps")
    ablation_dir = os.path.join(args.output_dir, "ablation")
    trainlog_dir = os.path.join(args.output_dir, "training_curves")

    pairs = collect_test_pairs(args.example_dir, n_pairs=4)

    steg = ImageSteganography(h_model_path=args.h_model, r_model_path=args.r_model)

    base_results = run_inference_on_pairs(steg, pairs, infer_dir, password=args.password)

    metrics_rows = [
        {
            "sample_id": r.sample_id,
            "cover_path": r.cover_path,
            "secret_path": r.secret_path,
            "stego_path": r.stego_path,
            "revealed_path": r.revealed_path,
            "psnr_cover_stego": r.psnr_cover_stego,
            "psnr_secret_revealed": r.psnr_secret_revealed,
            "ssim_secret_revealed": r.ssim_secret_revealed,
        }
        for r in base_results
    ]
    write_csv(
        os.path.join(args.output_dir, "inference_metrics.csv"),
        metrics_rows,
        [
            "sample_id",
            "cover_path",
            "secret_path",
            "stego_path",
            "revealed_path",
            "psnr_cover_stego",
            "psnr_secret_revealed",
            "ssim_secret_revealed",
        ],
    )

    plot_sample_curves(base_results, os.path.join(args.output_dir, "inference_psnr_ssim_curves.png"))

    capture_feature_maps(steg, pairs[0][1], pairs[0][2], feature_dir, password=args.password)

    ablation_rows = run_ablation(steg, pairs, ablation_dir)
    write_csv(
        os.path.join(args.output_dir, "ablation_study.csv"),
        ablation_rows,
        ["setting", "mean_psnr_cover_stego", "mean_psnr_secret_revealed", "mean_ssim_secret_revealed", "mean_runtime_ms"],
    )
    write_ablation_markdown(ablation_rows, os.path.join(args.output_dir, "ablation_study.md"))

    parse_training_logs_for_curves("d:/Stegen", trainlog_dir)

    write_security_analysis(base_results, ablation_rows, os.path.join(args.output_dir, "security_analysis.md"))

    summary = summarize_results(base_results)
    with open(os.path.join(args.output_dir, "summary.txt"), "w", encoding="utf-8") as f:
        for key, value in summary.items():
            f.write(f"{key}={value:.6f}\n")

    print("Evaluation completed.")
    print(f"Output directory: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
