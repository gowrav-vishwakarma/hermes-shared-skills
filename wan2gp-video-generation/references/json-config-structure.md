{
  "tasks": [
    {
      "model_type": "qwen_image_edit_plus2_20B",
      "model_filename": "https://huggingface.co/DeepBeepMeep/Qwen_image/resolve/main/qwen_image_edit_plus2_20B_quanto_bf16_int8.safetensors",
      "prompt": "Cinematic medium shot, 9:16 portrait. A simple studio set. The character_girl (image 1) and character_geek_boy (image 2) stand side-by-side, while the base character (image 3) stands slightly in front, waving cheerfully with a bright infectious grin. High-quality Pixar-style 3D animation, clean studio background, professional lighting, vibrant colors.",
      "guidance_scale": 4,
      "num_inference_steps": 30,
      "video_prompt_type": "I",
      "image_refs": [
        "/home/gowrav/.hermes/profiles/gvs/home/assets/character_girl.png",
        "/home/gowrav/.hermes/profiles/gvs/home/assets/character_geek_boy.png",
        "/home/gowrav/.hermes/profiles/gvs/home/character.png"
      ],
      "output_filename": "intro_anchor"
    }
  ]
}