#!/usr/bin/env python3  # noqa: EXE001
"""Created on July 1, 2025.

Script to correct and downsample BRPHYS DWL files: Background files.

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
TRUNCATED_ROWS = 3000
DOWNSAMPLED_ROWS = 500
DOWNSAMPLE_FACTOR = TRUNCATED_ROWS // DOWNSAMPLED_ROWS


# ===============================================
# Downsampling function
# ===============================================
def downsample_blockwise(data: np.ndarray, factor: int) -> np.ndarray:
    """Downsample a 1D array by averaging blocks of size 'factor'."""
    n_blocks = data.shape[0] // factor
    downsampled = np.zeros(n_blocks)
    for i in range(n_blocks):
        block = data[i * factor : (i + 1) * factor]
        downsampled[i] = block.mean()
    return downsampled


# ===============================================
# File processor
# ===============================================
def process_back_file(filepath: Path, output_dir: Path) -> Path:
    """Process a single Back*.txt file and write downsampled version."""
    # Load data
    data = np.loadtxt(filepath, dtype=float)

    # Truncate
    data = data[:TRUNCATED_ROWS]

    # Downsample
    data_ds = downsample_blockwise(data, DOWNSAMPLE_FACTOR)

    # Prepare output lines
    cleaned_lines = [f"{val:.6f}\n" for val in data_ds]

    # Destination path
    dst = output_dir / filepath.name
    output_dir.mkdir(parents=True, exist_ok=True)

    dst.write_text("".join(cleaned_lines), encoding="utf-8")
    logger.info("Processed %s → %s", filepath, dst)
    return dst


# ===============================================
# Bulk processor
# ===============================================
def process_all_back_files(source_dir: Path, target_dir: Path, pattern: str) -> None:
    """Process all files - pipeline."""
    files = list(Path(source_dir).rglob(pattern))
    logger.info("Found %d files in %s", len(files), source_dir)

    for file in files:
        try:
            process_back_file(file, target_dir)
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
    FILE_MASK = "Back*.txt"

    process_all_back_files(SOURCE_DIR, TARGET_DIR, FILE_MASK)
