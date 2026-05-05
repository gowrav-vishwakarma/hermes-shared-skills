#!/usr/bin/env python3
"""
Fix multi-LoRA CLI bug in video_generation.json.

Bug: generate_video_config.py concatenates space-separated LoRA filenames
into a single string in activated_loras array instead of separate entries.

Example broken state:
  "activated_loras": ["Pixar_Toon.safetensors LTX2.3_Crisp_Enhance.safetensors"]

Fixed state:
  "activated_loras": ["Pixar_Toon.safetensors", "LTX2.3_Crisp_Enhance.safetensors"]

Usage:
  python3 fix_multi_lora.py <path_to_video_generation.json>
"""
import json
import sys

def fix_multi_lora(config_path):
    with open(config_path, "r") as f:
        data = json.load(f)

    original = data.get("activated_loras", [])
    if not isinstance(original, list) or len(original) != 1:
        print(f"  No issue found. activated_loras = {original}")
        return False

    lora_str = original[0]
    if " " not in lora_str:
        print(f"  No issue found. activated_loras = {original}")
        return False

    # Split concatenated LoRAs
    fixed = [l.strip() for l in lora_str.split(" ")]
    data["activated_loras"] = fixed

    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"  BEFORE: {original}")
    print(f"  AFTER:  {data['activated_loras']}")
    print("  Fixed!")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path_to_video_generation.json>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    fix_multi_lora(config_path)
