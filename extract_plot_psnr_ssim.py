import argparse
import csv
import glob
import math
import os
import re
from typing import Dict, List


def safe_float(value: str):
    try:
        return float(value)
    except Exception:
        return None


def mse_to_psnr(mse: float):
    if mse is None or mse <= 0:
        return None
    return 10.0 * math.log10(1.0 / mse)


def parse_log_file(path: str):
    val_pattern = re.compile(
        r"validation\[(?P<epoch>\d+)\]\s+val_Hloss\s*=\s*(?P<hloss>[0-9.eE+-]+)\s*\t?\s*val_Rloss\s*=\s*(?P<rloss>[0-9.eE+-]+)\s*\t?\s*val_Sumloss\s*=\s*(?P<sumloss>[0-9.eE+-]+)",
        re.IGNORECASE,
    )
    psnr_pattern = re.compile(r"(psnr(?:_[a-z]+)?|val_psnr(?:_[a-z]+)?)\s*[:=]\s*([0-9.eE+-]+)", re.IGNORECASE)
    ssim_pattern = re.compile(r"(ssim(?:_[a-z]+)?|val_ssim(?:_[a-z]+)?)\s*[:=]\s*([0-9.eE+-]+)", re.IGNORECASE)

    rows: List[Dict] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            val_match = val_pattern.search(line)
            if not val_match:
                continue
            epoch = int(val_match.group("epoch"))
            hloss = safe_float(val_match.group("hloss"))
            rloss = safe_float(val_match.group("rloss"))
            sumloss = safe_float(val_match.group("sumloss"))

            row = {
                "source_log": path,
                "epoch": epoch,
                "val_hloss": hloss,
                "val_rloss": rloss,
                "val_sumloss": sumloss,
                "psnr_cover_container": mse_to_psnr(hloss),
                "psnr_secret_revealed": mse_to_psnr(rloss),
                "psnr_any": None,
                "ssim_any": None,
            }

            psnr_matches = psnr_pattern.findall(line)
            ssim_matches = ssim_pattern.findall(line)
            if psnr_matches:
                row["psnr_any"] = safe_float(psnr_matches[0][1])
            if ssim_matches:
                row["ssim_any"] = safe_float(ssim_matches[0][1])

            rows.append(row)

    return rows


def write_csv(rows: List[Dict], out_csv: str):
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    fieldnames = [
        "source_log",
        "epoch",
        "val_hloss",
        "val_rloss",
        "val_sumloss",
        "psnr_cover_container",
        "psnr_secret_revealed",
        "psnr_any",
        "ssim_any",
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def plot_curves(rows: List[Dict], out_dir: str):
    import matplotlib.pyplot as plt

    rows = sorted(rows, key=lambda item: item["epoch"])
    epochs = [item["epoch"] for item in rows]
    psnr_cover = [item["psnr_cover_container"] for item in rows]
    psnr_secret = [item["psnr_secret_revealed"] for item in rows]
    ssim_any = [item["ssim_any"] for item in rows]

    os.makedirs(out_dir, exist_ok=True)

    plt.figure(figsize=(8, 5))
    plt.plot(epochs, psnr_cover, marker="o", label="PSNR Cover-Container (from Hloss)")
    plt.plot(epochs, psnr_secret, marker="o", label="PSNR Secret-Revealed (from Rloss)")
    plt.xlabel("Epoch")
    plt.ylabel("PSNR (dB)")
    plt.title("PSNR Curves")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "psnr_curves.png"), dpi=150)
    plt.close()

    if any(value is not None for value in ssim_any):
        plt.figure(figsize=(8, 5))
        plt.plot(epochs, ssim_any, marker="o", label="SSIM")
        plt.xlabel("Epoch")
        plt.ylabel("SSIM")
        plt.title("SSIM Curve")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "ssim_curve.png"), dpi=150)
        plt.close()
    else:
        note_path = os.path.join(out_dir, "ssim_curve_note.txt")
        with open(note_path, "w", encoding="utf-8") as handle:
            handle.write("No SSIM values found in logs.\n")
            handle.write("Current training logs record losses; SSIM must be logged during training to plot this curve.\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Root folder to search logs")
    parser.add_argument("--log-glob", default="**/*_log.txt", help="Glob for training logs")
    parser.add_argument("--out-dir", default="analysis", help="Output directory for CSV and plots")
    args = parser.parse_args()

    pattern = os.path.join(args.root, args.log_glob)
    log_files = glob.glob(pattern, recursive=True)

    all_rows: List[Dict] = []
    for log_file in log_files:
        all_rows.extend(parse_log_file(log_file))

    if not all_rows:
        print("No validation log rows found.")
        print(f"Searched pattern: {pattern}")
        return 1

    out_csv = os.path.join(args.out_dir, "metrics_extracted.csv")
    write_csv(all_rows, out_csv)
    plot_curves(all_rows, args.out_dir)

    print(f"Parsed logs: {len(log_files)}")
    print(f"Extracted rows: {len(all_rows)}")
    print(f"Saved CSV: {out_csv}")
    print(f"Saved plots in: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
