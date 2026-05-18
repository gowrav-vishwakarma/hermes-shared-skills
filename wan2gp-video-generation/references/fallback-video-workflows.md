# Fallback Video Generation: Manim for Standalone 20s Videos

## When to use manim instead of WanGP

**Use manim when:**
- WanGP/Wan2GP is not set up or unavailable
- You need a **standalone text-to-video** without character references
- Video is **≤20 seconds** (single scene, narrative)
- You need **precise visual control** (cyberpunk scenes, UI overlays, animations)
- Faster turnaround (2-3 min vs 5-10 min WanGP setup)

## Manim workflow for standalone scenes

### 1. Create project folder
```bash
mkdir -p ~/posts/$(date +%Y-%m-%d)/scifi_2050_robots
cd ~/posts/$(date +%Y-%m-%d)/scifi_2050_robots
```

### 2. Write script.py
```python
from manim import *

class SciFiCity(Scene):
    def construct(self):
        # Add cityscape background with neon lights
        # Add robot figures with glowing AI cores
        # Add human figures hiding in shadows
        # Add camera pan and lighting effects
        pass
```

### 3. Render
```bash
cd /home/gowrav/.local/bin
manim -pql script.py SciFiCity
```

## Recommended manim scenes for 20s standalone videos

| Scene Type | Visual Elements | Duration |
|------------|----------------|----------|
| Dystopian city | Neon lights, rain, dark streets | 20s |
| Robot patrol | Glowing eyes, metallic bodies, scanning | 20s |
| Human hiding | Shadowy figures, debris, fear | 20s |
| HUD overlay | Math animations, neural feeds, tech UI | 20s |

## Key advantages over WanGP for standalone videos

- **No setup required** - manim is already installed globally
- **Precise control** - you define exactly what appears on screen
- **Faster iteration** - 2-3 min render vs 5-10 min setup + gen
- **Consistent style** - same aesthetic across all standalone videos
- **No VRAM issues** - CPU rendering fallback available

## When NOT to use manim

- Character reference videos (use WanGP with LoRA)
- Multi-scene narratives (use WanGP sliding window)
- Photorealistic cinematography (use WanGP LTX-2.3)
