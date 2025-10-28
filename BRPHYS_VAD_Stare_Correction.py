#!/usr/bin/env python3  # noqa: EXE001

"""Created on July 1, 2025.

Script to correct and downsample BRPHYS DWL files: VAD and Stare.

@author: Jonnathan Cespedes <j.cespedes@reading.ac.uk>
"""

from __future__ import annotations

import logging
from pathlib import Path

import click
import numpy as np

# ================================
# Setup logging
# ================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ================================
# Constants
# ================================
EXPECTED_NUM_GATES = 201
TRUNCATED_GATES = 3000
DOWNSAMPLED_GATES = 500
DOWNSAMPLE_FACTOR = TRUNCATED_GATES // DOWNSAMPLED_GATES
RAY_HEADER_LEN = 5
GATE_LINE_LEN = 4
source_root = Path(
    "/storage/research/actual01/disk1/urban/obs/LiDAR/Bristol/BRPHYS",
)


# ================================
# Downsampling helpers
# ================================
def downsample_ray_preserve_format(
    gate_lines: list[str],
    factor: int = DOWNSAMPLE_FACTOR,
) -> list[str]:
    """Downsample a lidar ray preserving original format."""
    data = np.array(
        [
            list(map(float, line.strip().split()[1:]))  # skip gate index
            for line in gate_lines[:TRUNCATED_GATES]
        ],
    )

    n_blocks = len(data) // factor
    downsampled = []

    for i in range(n_blocks):
        block = data[i * factor : (i + 1) * factor]
        avg_vals = block.mean(axis=0)
        # Preserve formatting: 3-digit gate, aligned floats
        line = f"  {i:>3d} {avg_vals[0]:7.4f} {avg_vals[1]:9.6f} {avg_vals[2]:13.6E}\n"
        downsampled.append(line)

    return downsampled


# ================================
# Main processing function
# ================================
def clean_hpl_file(  # noqa: C901, PLR0912
    filepath: str | Path,
    output_dir: str | Path,
) -> Path:
    """Fix header, truncate rays, and downsample to reduced gate count."""
    src = Path(filepath)
    dst = Path(output_dir) / src.relative_to(source_root)
    dst.parent.mkdir(parents=True, exist_ok=True)

    lines = src.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)

    current_gates = None
    gate_line_index: int | None = None
    header_end_idx: int | None = None
    cleaned_lines: list[str] = []

    # == Header pass ==================================─
    for idx, line in enumerate(lines):
        if line.startswith("Number of gates:"):
            current_gates = int(line.split(":")[1].strip())
            gate_line_index = len(cleaned_lines)
            cleaned_lines.append(line)  # Placeholder to replace later
        elif line.startswith("Range gate length (m):"):
            value = float(line.split(":")[1].strip())
            cleaned_lines.append(f"Range gate length (m):\t{int(value)}\n")
        else:
            cleaned_lines.append(line)

        if line.strip() == "****":
            header_end_idx = idx
            break

    if current_gates is None or header_end_idx is None or gate_line_index is None:
        msg = "Missing 'Number of gates:' or '****' in header."
        raise ValueError(msg)

    if current_gates <= EXPECTED_NUM_GATES:
        logger.info(
            "File has %s gates (≤ %s). No changes made: %s",
            current_gates,
            EXPECTED_NUM_GATES,
            src,
        )
        return src

    # == Ray processing ================================
    ray_header: str | None = None
    gate_lines: list[str] = []

    for line in lines[header_end_idx + 1 :]:
        parts = line.strip().split()
        if len(parts) == RAY_HEADER_LEN:
            if ray_header is not None:
                cleaned_lines.append(ray_header + "\n")
                cleaned_lines.extend(downsample_ray_preserve_format(gate_lines))
            ray_header = line.strip()
            gate_lines = []
        elif len(parts) == GATE_LINE_LEN:
            gate_lines.append(line)
        else:
            continue  # ignore malformed lines

    # Final ray
    if ray_header is not None:
        cleaned_lines.append(ray_header + "\n")
        cleaned_lines.extend(downsample_ray_preserve_format(gate_lines))

    # Replace Number of gates with the downsampled count
    cleaned_lines[gate_line_index] = f"Number of gates:\t{DOWNSAMPLED_GATES}\n"

    dst.write_text("".join(cleaned_lines), encoding="utf-8")
    logger.info("Cleaned and downsampled: %s → %s", src, dst)
    return dst


# ================================
# Bulk processor
# ================================
def process_all_hpl_files(
    source_dir: str | Path,
    target_dir: str | Path,
    pattern: str,
) -> None:
    """Apply clean_hpl_file() to all matching files in subfolders."""
    files = list(Path(source_dir).rglob(pattern))
    logger.info("Found %d .hpl files in %s", len(files), source_dir)

    for file in files:
        try:
            clean_hpl_file(file, target_dir)
        except Exception:
            logger.exception("Failed to process %s", file)


# ================================
# Entrypoint
# ================================
@click.command()
@click.option(
    "--prefix",
    prompt="Enter file prefix (e.g., Wind or Stare)",
    help="Prefix of .hpl files ('Wind' -> 'Wind_*.hpl' or 'Stare' -> 'Stare_*.hpl')",
)
def main(prefix: str) -> None:
    """Command-line interface for processing DWL .hpl files."""
    target_root = Path(
        "/storage/research/actual01/disk1/urban/obs/LiDAR/Bristol/BRPHYS_co",
    )
    mask_file = f"{prefix}_*.hpl"
    logger.info("Using pattern: %s", mask_file)
    process_all_hpl_files(source_root, target_root, mask_file)


if __name__ == "__main__":
    main()
