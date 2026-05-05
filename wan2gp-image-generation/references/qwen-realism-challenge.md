# Qwen Image Edit Plus 2511 — Realism Challenge

## Session Evidence (2026-05-05)

User rejected generated location assets for being too "perfect" and AI-looking:
- **Session 2026-05-05_5**: `location_jungle_river` — too saturated, uniform stones, "glow" bloom effect, unnatural clarity
- **Session 2026-05-05_5 (retry)**: `location_river_realistic` — still had hyper-clarity, smooth uniform foreground, dappled light "glow"

## Root Cause

Qwen Image Edit Plus 2511 inherently produces hyper-perfect, glossy aesthetics:
- Water that's "too clear" (every pebble visible, impossible in nature)
- Uniform stone sizes and shapes
- Saturated, uniform greens
- Specific "bloom/glow" lighting signature common in AI art
- Smooth, perfect foreground textures

## Workaround Strategy

To push toward documentary/photorealistic look, explicitly prompt for:

1. **Camera specs**: "Shot on Canon EOS R5, 35mm lens, natural light"
2. **Imperfections**: "muddy banks", "dead leaves scattered", "rough bark texture", "slight film grain"
3. **Natural chaos**: "scattered rocks of various sizes", "uneven water depth", "debris in water"
4. **Anti-perfection**: "not crystal-perfect", "gentle ripples and slight reflection", "nothing overly saturated"
5. **Reference style**: "documentary photography", "natural colors", "like a real photograph taken by a nature photographer"

Even with these prompts, Qwen still produces noticeable AI-hallmarks (hyper-clarity, texture uniformity). The best approach is to:
- Accept the "AI-ish" quality and work with it
- Focus on composition and subject matter over photorealism
- Use post-processing or masking if realism is critical
- Consider that the realism target may not be achievable with this model alone
