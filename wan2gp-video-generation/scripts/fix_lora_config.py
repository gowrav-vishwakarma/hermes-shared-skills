#!/usr/bin/env python3
"""Fix multi-LoRA config in video_generation.json.

The generate_video_config.py CLI sometimes merges multiple LoRA filenames
into one space-separated string inside the activated_loras array:
    ["Pixar_Toon.safetensors LTX2.3_Crisp_Enhance.safetensors"]

This script splits them back into separate items and verifies
the multipliers match.

Usage:
    python3 fix_lora_config.py <path_to_video_generation.json>

Example:
    python3 fix_lora_config.py posts/2026-05-02_4/video_generation.json
"""

import json
import sys


def fix_lora_config(config_path):
    with open(config_path, "r") as f:
        data = json.load(f)

    loras = data.get("activated_loras", [])
    multipliers = data.get("loras_multipliers", "")

    # Check if any entry has spaces (merged filenames)
    merged = False
    fixed_loras = []
    for entry in loras:
        if isinstance(entry, str) and " " in entry:
            fixed_loras.extend(entry.split(" "))
            merged = True
        else:
            fixed_loras.append(entry)

    if merged:
        data["activated_loras"] = fixed_loras
        print(f"  Fixed: merged LoRA names split into {len(fixed_loras)} items")

    # Verify multiplier count matches
    multiplier_list = [m.strip() for m in multipliers.split(";") if m.strip()]
    if len(fixed_loras) != len(multiplier_list):
        print(f"  WARNING: {len(fixed_loras)} LoRAs but {len(multiplier_list)} multipliers!")
        print(f"  LoRAs: {fixed_loras}")
        print(f"  Multipliers: {multiplier_list}")
    else:
        print(f"  OK: {len(fixed_loras)} LoRAs match {len(multiplier_list)} multipliers")

    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"  Saved: {config_path}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    fix_lora_config(sys.argv[1])
