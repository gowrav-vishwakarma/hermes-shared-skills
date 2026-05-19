# Anatomy Control for Anthropomorphic Characters

## The Problem

LTX-2.3 consistently struggles with limb counts on anthropomorphized animals (bipedal animals, characters with trunks/proboscis/accessories). The model tends to add extra legs or arms when:
- Animals have accessories on lower body (rain boots, shoes)
- Characters use trunks/proboscis for interaction (elephant with lantern)
- Multiple complex body parts are described (limbs + accessories + held objects)

## Evidence

**Session 2026-05-18:** Baby elephant with lantern video required iteration because the first attempts didn't clearly show "exactly two legs, two arms, trunk holding lantern." The model kept producing ambiguous anatomy.

## Solution: Explicit Anatomy Locking

In the prompt, add a dedicated anatomy directive at the END of the prompt (after all scene description):

```
EXACTLY two legs, exactly two arms, trunk holding lantern — no extra limbs, no messy anatomy, clear four-limb structure.
```

### Anatomy directive template

Replace the generic part with your specific character:

| Character | Anatomy directive |
|---|---|
| Bipedal animal | `EXACTLY two legs, no tail touching ground, two arms — no extra limbs` |
| Quadruped animal | `EXACTLY four legs, no arms, no human-like limbs — animal quadruped anatomy only` |
| Elephant with trunk | `EXACTLY two legs, two arms, trunk holding [OBJECT] — no extra limbs, no messy anatomy` |
| Two characters | `EXACTLY two legs each, clear separation between the two characters — no merged limbs` |
| Dog walking upright | `EXACTLY two hind legs standing, two front paws visible — no extra legs, canine anatomy` |

### Key principles

1. **Add anatomy directive at the END** of the prompt — after all scene/camera/lighting description. This acts as a final override.
2. **Use exact numbers** — "exactly two legs", not "on two legs". The word "exactly" helps.
3. **Negate the wrong thing** — "no extra limbs, no messy anatomy, clear four-limb structure".
4. **Specify what IS correct** — "trunk holding lantern" clarifies the trunk's role so the model doesn't mistake it for an arm.
5. **For animals with trunks/proboscis** — explicitly state the trunk's function so the model doesn't count it as an additional limb.
6. **Consider using I2V with anchor** — if anatomy still fails, generate an anchor image first (via ComfyUI for stylized output) with correct anatomy, then do I2V. The anchor acts as frame 0 and locks character structure.

### When anatomy prompts aren't enough

If anatomy still fails after explicit prompting:
1. Switch to **I2V with anchor image** — generate the correct pose first
2. Try **different seed** — some seeds handle complex anatomy better
3. Try **lower LoRA multiplier** — high multiplier (1.5+) can sometimes distort anatomy further
4. For character consistency: use `--image-start` with a correct anchor as frame 0