# Character Asset Registration

Pattern for registering new character images for use in WanGP image/video generation.

## When to register

A character image should be registered as an asset when:
- It will be referenced by name (e.g., `character_ginnie`) in image/video prompts
- It needs to be reused across multiple scenes or posts
- The user wants a persistent character identity

## Step 1: Save the image

Copy the character image to the assets folder:

```bash
cp "<source_image>" /home/gowrav/.hermes/profiles/gvs/home/assets/<character_name>.png
```

The file extension should be `.png` for consistency with existing assets.

## Step 2: Register in assets.json

Edit `/home/gowrav/.hermes/profiles/gvs/home/assets/assets.json` and add an entry:

```json
"<character_name>": {
  "path": "/home/gowrav/.hermes/profiles/gvs/home/assets/<character_name>.png",
  "kind": "character",
  "aspect": "<ASPECT_RATIO>",
  "description": "<Brief visual description for prompt references>",
  "tags": [
    "character",
    "<descriptor_1>",
    "<descriptor_2>",
    "avatar"
  ],
  "parent_refs": [],
  "source_post": "<source>",
  "created": "<YYYY-MM-DD>"
}
```

### Field notes
- **`aspect`**: Image aspect ratio (e.g., `9:16`, `4:5`, `1:1`)
- **`description`**: Concise visual summary — key distinguishing features the prompt can reference later
- **`tags`**: At minimum include `character` and `avatar`; add descriptors as needed
- **`source_post`**: `"manual"` for manually saved images, or the post name for auto-generated anchors
- **`created`**: Date the asset was registered

## Step 3: Use in prompts

Reference the character by name in image/video prompts:

```
The character_ginnie (image N) stands confidently with arms crossed...
```

The `image N` index refers to the position in the `image_refs` array of the generation config, matching the order of characters listed.

## Existing characters

- `character_base` — Middle-aged man, glasses, serious
- `character_girl` — Young woman, casual outfit
- `character_geek_boy` — Young man, tech outfit, glasses
- `character_ginnie` — Blue genie/djinn, gold accessories, snake tail
