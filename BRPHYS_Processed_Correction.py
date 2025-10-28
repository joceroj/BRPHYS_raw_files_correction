#!/usr/bin/env python3  # noqa: EXE001
"""Created on July 1, 2025.

Script to correct and downsample BRPHYS DWL files: Processed wind profiles.

@author: Jonnathan Cespedes <j.cespedes@reading.ac.uk>
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

# ===============================================
# Setup logging
# ===============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ===============================================
# Constants
# ===============================================

TRUNCATED_ROWS = 2010
DOWNSAMPLED_ROWS = 335
DOWNSAMPLE_FACTOR = TRUNCATED_ROWS // DOWNSAMPLED_ROWS


# ===============================================
# Helper for circular mean of wind direction
# ===============================================
def circular_mean_deg(angles: np.ndarray) -> float:
    """Compute circular mean of angles in degrees."""
    radians = np.deg2rad(angles)
    mean_sin = np.mean(np.sin(radians))
    mean_cos = np.mean(np.cos(radians))
    mean_angle = np.arctan2(mean_sin, mean_cos)
    return np.rad2deg(mean_angle) % 360


# ===============================================
# Downsampling function
# ===============================================
def downsample_blockwise(data: np.ndarray, factor: int) -> np.ndarray:
    """Downsample data by averaging blocks of size 'factor'."""
    n_blocks = data.shape[0] // factor
    downsampled = []

    for i in range(n_blocks):
        block = data[i * factor : (i + 1) * factor]
        mean_range = block[:, 0].mean()
        mean_dir = circular_mean_deg(block[:, 1])
        mean_speed = block[:, 2].mean()
        downsampled.append([mean_range, mean_dir, mean_speed])

    return np.array(downsampled)


# ===============================================
# File processor
# ===============================================
def process_file(filepath: Path, output_dir: Path) -> Path:
    """Process a single file and write downsampled version."""
    lines = filepath.read_text(encoding="utf-8", errors="ignore").splitlines()

    # Header (first row)
    try:
        n_gates = int(lines[0].strip())
    except ValueError as e:
        msg = f"Invalid header in {filepath}: {lines[0]}"
        raise ValueError(msg) from e

    n_gates = min(n_gates, DOWNSAMPLED_ROWS)

    # Load data (skip header row)
    data = np.loadtxt(lines[1:], dtype=float)
    if data.ndim == 1:  # ensure 2D in case of single row
        data = data.reshape(1, -1)

    # Truncate
    data = data[:TRUNCATED_ROWS, :]

    # Downsample
    data_ds = downsample_blockwise(data, DOWNSAMPLE_FACTOR)

    # Prepare output
    cleaned_lines = [f"{n_gates}\n"]
    cleaned_lines.extend(f"{row[0]:.3f} {row[1]:.3f} {row[2]:.3f}\n" for row in data_ds)

    # Destination path
    dst = output_dir / filepath.name
    output_dir.mkdir(parents=True, exist_ok=True)

    dst.write_text("".join(cleaned_lines), encoding="utf-8")
    logger.info("Processed %s → %s", filepath, dst)
    return dst


# ===============================================
# Bulk processor
# ===============================================
def process_all_files(source_dir: Path, target_dir: Path, pattern: str) -> None:
    """Process all files - pipeline."""
    files = list(Path(source_dir).rglob(pattern))
    logger.info("Found %d files in %s", len(files), source_dir)

    for file in files:
        try:
            process_file(file, target_dir)
        except Exception:
            logger.exception("Failed to process %s", file)


# ===============================================
# Entrypoint
# ===============================================
if __name__ == "__main__":
    SOURCE_DIR = Path(
        "/storage/research/actual01/disk1/urban/obs/LiDAR/Bristol/BRPHYS",
    )
    TARGET_DIR = Path(
        "/storage/research/actual01/disk1/urban/obs/LiDAR/Bristol/BRPHYS_co",
    )
    FILE_MASK = "Proce*.hpl"

    process_all_files(SOURCE_DIR, TARGET_DIR, FILE_MASK)
