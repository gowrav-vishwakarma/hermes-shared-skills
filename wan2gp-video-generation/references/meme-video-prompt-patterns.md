# Meme-to-Video and Dialogue Scene Prompts

## When to use

Converting static meme images into 20s videos with dialogue and character movement.

## Prompt structure (3-part formula)

Every dialogue/meme video prompt needs:

### 1. Scene Setup (who, where, where)

```
Cinematic 16:9 medium shot. THREE CHARACTERS, LEFT TO RIGHT:
- On the FAR LEFT — [description: clothing, hair, position, action]
- In the CENTER — [description: clothing, position, posture]
- On the FAR RIGHT — [description: clothing, position, expression]
```

### 2. Movement Beats (what each character does)

```
MOVEMENT BEATS:
- Character A slowly [action: head turn, smirk, gesture]
- Character B [action: raises hand, jaw drops, shakes head]
- Character C [action: winks, turns back, blows kiss]
Camera slowly [movement: dolly-forward, pan, zoom]
```

### 3. Dialogue (in quotes, with speaker attribution)

```
AUDIO — [speaker] says "quoted dialogue here."
[Next speaker] responds: "more dialogue."
```

**Rules for dialogue:**
- Use `"` for spoken quotes (not single quotes)
- Attribute each line to the speaker before or after the quote
- Keep total dialogue within 20s single-pass (no repetition)
- End with a visual beat (no dialogue) if video is longer than dialogue

## Complete example (Distracted Boyfriend meme)

```
Cinematic 16:9 medium shot of three people on a city street. THREE CHARACTERS, LEFT TO RIGHT:
On the FAR LEFT — woman in a bright red sleeveless dress, long brown hair, walking AWAY from camera toward the left edge of frame, smiling happily, completely unaware of what's behind her.
In the CENTER — young man in a blue and white plaid short-sleeve shirt, body facing forward-left following the woman in red, but his HEAD is snapped back sharply over his RIGHT shoulder, neck twisted, eyes WIDE and locked on the woman in red, mouth slightly open in disbelief.
On the FAR RIGHT — his girlfriend in a light blue sleeveless tank top and blue jeans, long brown hair, standing behind the man, staring at HIM (not at the woman in red), her expression a mix of shock, betrayal, and comical anger.

MOVEMENT BEATS:
The man slowly turns his head EVEN FURTHER back, a guilty but amused smirk spreading across his face. His eyes practically sparkle as he stares at the woman in red.
The girlfriend slowly raises ONE HAND to her mouth in shock, her eyebrows shoot up higher, her jaw drops. She starts to gesture with both hands, palms up, shaking her head.
The woman in red senses someone looking, turns her head back over her left shoulder, gives a playful wink at the camera, and blows a quick kiss.
Camera slowly DOLLY-FORWARD, building comedic tension like a soap opera cliffhanger.

AUDIO — girlfriend shouts 'Wait... are you LOOKING at her?!'
The boyfriend tries to play it cool, chuckling nervously: 'Me? No. I just... uh...'
The girlfriend interrupts, voice rising: 'YOU WERE STARING AT HER IN MY FACE!'
The boyfriend sheepishly admits: 'Okay yes. She had a RED DRESS. You know how I feel about red.'
The girlfriend crosses her arms and says deadpan: 'Get her number. I'm leaving.'
The boyfriend calls out: 'Excuse ME — do you have a date?' as the woman in red smiles and turns away.
Audio: comedic background music, light footsteps, girlfriend's frustrated sigh.
```

## Key patterns

- **Explicit positional markers**: "FAR LEFT", "CENTER", "FAR RIGHT" — LTX-2.3 needs clear spatial anchors
- **Movement beats section**: Separate paragraph describing physical actions the model should animate
- **Dialogue attribution**: "[speaker] says/shouts/responds/calls out" before or after quotes
- **Audio tag at end**: Summarize music, SFX, and ambient sounds

## Common pitfalls

1. **No positional markers** — Model doesn't know who is where, characters swap places mid-video
2. **Dialogue without attribution** — LTX-2.3 can't tell which voice to use for which quote
3. **No movement beats** — Characters stay static/talking-heads without explicit motion cues
4. **Dialogue exceeds 20s** — LTX-2.3 loops the prompt. Keep dialogue tight or use sliding window with visual closing beat
5. **Single quotes inside shell** — If writing to `.txt` file, use `<< 'HEREDOC'` (quoted delimiter) for safe quoting

## Template for any meme-to-video

```
[Shot type] of [scene description]. [N] CHARACTERS:
- LEFT — [description]
- CENTER — [description]
- RIGHT — [description]

MOVEMENT BEATS:
- [Character 1] [specific movement]
- [Character 2] [specific movement]
- [Character 3] [specific movement]
Camera [camera movement].

AUDIO — [speaker 1]: "[dialogue 1]"
[speaker 2]: "[dialogue 2]"
[Closing beat — no dialogue]
Audio: [music/SFX description].
```
