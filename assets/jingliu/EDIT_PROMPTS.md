# 图像编辑提示词

模式：内置 image_gen，图像编辑，透明背景。所有参考文件与用途见 SOURCES.md。

## v1 抠图、补全与精修

```text
Edit the first referenced image, the selected chibi Jingliu illustration, into a meticulous transparent-background desktop-pet character asset.
Input roles:
1. jingliu_range0v0.jpg is THE EDIT TARGET and absolute authority for the chibi drawing, pose, proportions, facial expression, red eyes, line style and color placement. Preserve this specific illustration recognizably; this is a faithful cutout/restoration, not a new character drawing.
2. official_reference_1.webp is a costume and hair multi-view reference only: Jingliu's front, side and back, sleeve/gauntlet details.
3. official_reference_2.webp: ONLY use the TOP HALF for Jingliu's crystalline sword and the small Jingliu figure at top right. The lower half shows the DIFFERENT character Baiheng with fox ears. Ignore the entire lower half. Do not introduce fox ears, a tail, or Baiheng clothing.
4. official_portrait.webp is Jingliu's official outfit, accessory, hair and weapon visual reference only. Do not copy its adult proportions, action pose, lighting or effects.

Required edit:
- Precisely remove the entire blue striped/starry poster background and its rectangular white frame. Output true RGBA alpha transparency, no opaque background and no simulated checkerboard.
- Preserve the original very large rounded head, small body, soft pink cheek blush, relaxed half-lidded red eyes and small subtle smile; SAME face, SAME hair sweep, SAME standing pose.
- Preserve the original arm positions: viewer-left arm down holding the short icy sword angled down-left; viewer-right gloved hand bent across the chest.
- Recover the slight cropping at the top of the hair, sides of the long rear hair and ribbons, and bottom of BOTH boots. Expand the canvas as needed. Show the ENTIRE complete silhouette with 6-10 percent clear transparent margin all around. Do not crop hair, ribbon ends, sword tip or boots.
- Clean JPEG artifacts and sharpen the original dark outlines with consistent smooth anti-aliasing. Keep clean hand-drawn anime cel coloring, subtle original shading and fine hair strands rather than photorealistic or 3D texture.
- Refine details restrainedly using the official reference: asymmetrical blue sleeves and silver gauntlet ornament, dark high collar with gold/silver filigree, pale circular moon ornament at the waist, layered pale blue skirt with lavender underside, dark hanging costume panel with lunar decoration, silver waist ornament with red knot/tassel, ornate dark blue boots and blue rear hair ribbons. Keep the chibi simplification rather than introducing noisy tiny decorations.
- Complete the sword edges and small icy guard details in the existing short chibi sword, using the top-half weapon reference. Do not enlarge it into a giant adult sword or add a second sword.
- The chosen chibi is WITHOUT blindfold. Keep the red eyes fully visible. Do not add a blindfold.
- Hair white/silver with pale lavender-blue shadow; retain original dark blue/cobalt outfit with controlled gold/silver trim and red tassel. Retain existing two arms and two legs.
- Remove all leftover poster-colored specks or frame fragments between the limbs, hair, sleeves, tassel and blade. Thin semi-transparent antialiased hair edges are fine. No white/blue matte fringe, no white outline sticker border.
- No text, caption, labels, decorative scene elements, added sparks, cast ground shadow, glow cloud, UI, or alternate poses.
Return ONE high-resolution portrait PNG on a truly transparent background, ideally at least 1024x1536. This is a single restored flattened cutout, NOT an animation, sprite sheet, collage, or character turnaround.
```

## v2 高马尾修正

```text
EDIT the first image (jingliu_refinement_draft_v1.png). Make a focused hairstyle correction and finish the transparent cutout.
The second image (official_reference_1.webp) is the authoritative Jingliu hairstyle/costume reference. The third image (jingliu_range0v0.jpg) is the original chibi face/style reference, not a request to restore its cropped poster background.

Main correction requested by the user: SINGLE HIGH PONYTAIL (高马尾).
- Jingliu's long silver-white back hair must be gathered into ONE high ponytail. Show an unmistakable single gathering point high on the back of the head, ABOVE ear level close to the crown, secured by her blue ribbon/head ornament.
- Hair sweeps UP from the back of the head into the high tie; the long ponytail then arcs out behind the head and descends as ONE cohesive thick tapered flowing tail, primarily behind the character's right side in the image. A few separated tips within this one tail are natural.
- Do not leave two independent large curtains of loose hair falling from both sides of the scalp. No twin tails, no low ponytail, no pigtails, no loose waist-length back hair growing directly from the nape.
- Preserve the original long side-swept front bangs, the short cheek-framing sidelocks, her recognizable half-lidded red eyes, blush, tiny smile, very large head and tiny body, earring, same pose, same little down-left icy sword, same two arms and two legs, and all blue/black/silver/gold/red costume details. Keep the original cute 2D cel-painted drawing. No blindfold, no fox ears.

Cutout correction:
- Remove the entire blue-gray halo, blurred background, black vignette and any other exterior imagery from the first image. There must be NO blue smoke, NO gray glow, NO dark gradient behind the character.
- Deliver real alpha transparency: EVERY pixel outside the actual character/hair/ribbon/sword silhouette must be alpha=0, including gaps between the arm and body, boots, hair locks and fabric panels. Only the thin antialiasing at the outline may have partial alpha. Solid character interiors should be opaque.
- No drawn checkerboard, no background color, no ground shadow, no added scene, no outline sticker border.
- Frame one complete full-body character with all hair tips, high ponytail knot and ribbons, sword and both boot tips fully inside the canvas, and clear transparent breathing room of at least 5 percent on ALL four sides.
- Preserve the quality and identity of the source chibi. Refine contours cleanly but do not redesign the face, outfit, colors or pose.
Return ONE high resolution transparent portrait PNG. Not a sprite sheet, not an animation or multiple views.
```

