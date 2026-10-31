# 部件抠取与遮挡补全提示词

使用内置 image_gen 编辑工具；每个部件分别生成，transparent_background=true。已有原图、精修图和武器图均保留。像素检查只读取文件，未用代码重绘部件。

用户结构修正：紫色部分归裙摆，颜色最终保持原紫色；黑色月相飘带属于画面右侧手臂的衣袖延伸，不能和裙摆合并。

## head

```text
You are extracting ONE separate 2D animation layer from the provided already-approved chibi Jingliu artwork. This is an image-editing/animation-preparation task.
The image jingliu_cutout_refined_high_ponytail.png is the edit target and the authority for exact identity, drawing style, color and shape. Preserve its confident dark-navy outlines, soft cel coloring and Q proportions. Do not redesign the artwork or invent another pose.
Output one single part on a true transparent RGBA PNG canvas. No background, vignette, cloud, glow, floor shadow, gradient, checkerboard, text, labels, other parts, grids or multiple views.
Ideally keep the SAME 1024 x 1536 canvas as the source and the requested part at its original coordinate, orientation and scale, leaving deleted regions transparent. Do not enlarge or recenter the part just to fill the canvas. Retain clear antialiasing on the cut edge. Smoothly complete only small regions hidden by neighboring parts, for rotation overlap in a 2D rig; no exposed body reconstruction.

Extract only the COMPLETE HEAD layer: face with the same half-lidded red eyes, blush and tiny smile, silver-white front hair cap, side-swept bangs and short cheek-framing side locks, ears and the visible dangling earring.
EXCLUDE the long high ponytail behind the head, the ponytail's blue bow and trailing ribbons, the entire neck collar, torso, shoulders, arms, clothing, legs and sword.
Keep the exact face and expression. Cleanly finish the short back-of-head hair boundary that was covered by the ponytail. The face/hair should form a complete head that can tilt as one piece. It occupies roughly x 65..780 and y 50..695 in the source, with the bottom at the chin/side locks. Keep the upper crown intact. Do not add a blindfold or change the hairstyle's front silhouette.
```

## ponytail

```text
You are extracting ONE separate 2D animation layer from the provided already-approved chibi Jingliu artwork. This is an image-editing/animation-preparation task.
The image jingliu_cutout_refined_high_ponytail.png is the edit target and the authority for exact identity, drawing style, color and shape. Preserve its confident dark-navy outlines, soft cel coloring and Q proportions. Do not redesign the artwork or invent another pose.
Output one single part on a true transparent RGBA PNG canvas. No background, vignette, cloud, glow, floor shadow, gradient, checkerboard, text, labels, other parts, grids or multiple views.
Ideally keep the SAME 1024 x 1536 canvas as the source and the requested part at its original coordinate, orientation and scale, leaving deleted regions transparent. Do not enlarge or recenter the part just to fill the canvas. Retain clear antialiasing on the cut edge. Smoothly complete only small regions hidden by neighboring parts, for rotation overlap in a 2D rig; no exposed body reconstruction.

Extract only the SINGLE HIGH PONYTAIL layer behind the head, including its high gathering tuft/root, blue binding/bow and long blue ribbon ends.
The high tie is near x 575,y 55 of the source; the white/silver ponytail arcs from that high root and falls primarily down the RIGHT side of the image to near y 1100. Keep the single cohesive long white tail with its pale blue/lavender shaded tips and the blue ribbon design.
Remove the entire front hair/head/face and all ears, earring, torso, arms, clothes, legs and sword. Reconstruct the small hidden upper/back section so the isolated ponytail is continuous behind the front head. No second ponytail, no loose back-hair curtains, no face or wig mannequin. A single high ponytail with its tied ribbons only.
```

## torso

```text
You are extracting ONE separate 2D animation layer from the provided already-approved chibi Jingliu artwork. This is an image-editing/animation-preparation task.
The image jingliu_cutout_refined_high_ponytail.png is the edit target and the authority for exact identity, drawing style, color and shape. Preserve its confident dark-navy outlines, soft cel coloring and Q proportions. Do not redesign the artwork or invent another pose.
Output one single part on a true transparent RGBA PNG canvas. No background, vignette, cloud, glow, floor shadow, gradient, checkerboard, text, labels, other parts, grids or multiple views.
Ideally keep the SAME 1024 x 1536 canvas as the source and the requested part at its original coordinate, orientation and scale, leaving deleted regions transparent. Do not enlarge or recenter the part just to fill the canvas. Retain clear antialiasing on the cut edge. Smoothly complete only small regions hidden by neighboring parts, for rotation overlap in a 2D rig; no exposed body reconstruction.

Extract the CLOTHED CENTRAL TORSO BASE with front skirt as one animation layer: dark decorative high collar, modest blue/navy fitted front garment with gold/silver trim, circular pale moon waist ornament, central dark front panel and layered pale blue/lavender front skirt.
Retain original body proportions and all intact clothing motifs. Remove head/hair/earring, BOTH arms and gloved hands, both legs/boots, all rear trailing coat ribbons and the red waist tassel (it will be a separate piece), and all sword imagery.
Reconstruct only the CLOTHED regions covered by the bent hand/sleeve across the chest and the waist accessory so the decorated garment is continuous. Keep natural small overlap tabs at shoulders for attaching the arm layers; do not add arms or bare anatomy. Bottom skirt hem should remain the same. This clothed torso lies roughly x 215..655,y 610..1190 in the source. Transparent everywhere else.
```

## arm_viewer_left

```text
Extract ONE named animation layer from the attached already-approved chibi Jingliu illustration. Preserve the exact drawing, colors, pose and dark-navy cel-art outlines. This is animation material preparation, not a redesign.
Produce one single layer on a genuine transparent RGBA PNG. All unrelated areas deleted to alpha zero, including holes between the retained shapes. No background, glow, halo, vignette, fog, gradients, floor, checkerboard, text, multiple views, extra objects or full character.
Prefer the original 1024x1536 canvas with the layer at original coordinates and size. Complete only CLOTHING/accessory overlap hidden by other layers; retain the source's Q proportions and modest costume.

Keep ONLY the character's arm on the LEFT side of the picture (her right arm), from the shoulder joint down to the black gloved hand.
Include its pale-blue flower/pauldron at the shoulder, fitted royal blue sleeve, silver-edged angular forearm guard, black cuff and gloved hand in the original downward pose. Remove the icy sword from the hand entirely, leaving a natural curled empty grip for later prop attachment. Finish the glove at places where the grip was hidden.
Do not include head/hair, torso or skirt, neck, other arm, legs, the weapon or background. The retained limb runs from roughly x265,y675 to x145,y968 and is held diagonally down-left. Keep the ornate blue-and-silver gauntlet and original white-blue flower. The arm may have a small shoulder overlap tab for attachment, no other body part.
```

## arm_viewer_right

```text
Extract ONE named animation layer from the attached already-approved chibi Jingliu illustration. Preserve the exact drawing, colors, pose and dark-navy cel-art outlines. This is animation material preparation, not a redesign.
Produce one single layer on a genuine transparent RGBA PNG. All unrelated areas deleted to alpha zero, including holes between the retained shapes. No background, glow, halo, vignette, fog, gradients, floor, checkerboard, text, multiple views, extra objects or full character.
Prefer the original 1024x1536 canvas with the layer at original coordinates and size. Complete only CLOTHING/accessory overlap hidden by other layers; retain the source's Q proportions and modest costume.

Keep ONLY the arm on the RIGHT side of the picture (her left arm), including shoulder/sleeve, elbow, forearm and the dark gloved hand bent inward across the chest.
Preserve the original pose: elbow outward on the right; forearm crosses horizontally toward the left; curled glove near the center of the chest. Include the original blue sleeve, soft blue/lavender folds, silver cuff and dark-navy/gold shoulder trim.
Remove all torso/chest garment, waist moon ornament, neck, head/hair, the other arm, skirt, legs, rear ribbons and sword. Extend only a small shoulder attachment overlap, no extra anatomy. The shape lies roughly x395..693,y680..855 in the source. Do not straighten the arm or make a different hand gesture.
```

## skirt_back

```text
Extract ONLY the PURPLE REAR SKIRT FABRIC from the attached chibi Jingliu illustration into one transparent animation layer.
Critical human correction: the lavender-purple shapes behind the front skirt and legs are SKIRT HEM / rear skirt fabric. They are not hair, and they are not part of the black hanging sleeve ribbon.
KEEP THE ORIGINAL PURPLE/LAVENDER COLOR EXACTLY. Do NOT recolor it blue. Do NOT change the character's palette.
Retain only those lavender-purple flowing skirt panels/hem lobes below the waist and behind the legs. Reconstruct the small hidden skirt fabric behind the front skirt and legs to make a useful continuous rear-skirt overlap layer, with the same original folds, dark linework and subdued purple decoration. Keep it modest costume cloth.
DELETE ENTIRELY the black/navy diagonal strip with gold moon symbols and its blue/gold tip; that piece belongs to the arm sleeve, a DIFFERENT animation layer. Also delete all head/hair, torso front garment, white/pale-blue front skirt, arms, hands, legs, boots, red tassel and sword.
No new garment silhouette: use the source's purple skirt hem shape only. Keep the original source perspective and proportions as closely as possible. Do not include any white hair or blue ribbons.
Output ONE isolated purple rear-skirt layer, genuine transparent RGBA, ideally on the same 1024x1536 source canvas at the original relative placement. Exterior and gaps alpha zero. No backdrop, gray glow, gradient, shadow, checkerboard, text or character.
```

## sleeve_tail_viewer_right

```text
Extract ONLY the BLACK HANGING SLEEVE EXTENSION from the RIGHT arm of the attached chibi Jingliu illustration as a separate transparent animation layer.
Critical human correction: the dark diagonal ribbon with golden moon-phase motifs is a long extension of the RIGHT-SIDE ARM'S CLOTHING / sleeve. It does not grow from the waist or skirt. Its upper root attaches under the blue upper-arm/sleeve on the RIGHT side of the image. It hangs diagonally down-right and ends in the cobalt-blue gold-trimmed pointed decoration.
Keep the ORIGINAL black/navy, gold lunar motifs and blue terminal colors and exact clean chibi outline style. Preserve the sequence of moon decorations visible in the source, without adding more.
Provide a short dark fabric overlap/root tab at the top under the right arm sleeve so it can be attached there in an animation rig. Reconstruct the small hidden sleeve-ribbon root behind the foreground sleeve, not a waist attachment.
DELETE ALL purple/lavender skirt fabric. Delete every hair, head, face, torso, waist ornament, red tassel, skin, legs, boots, all hand/arm and blue main sleeve shapes, and the sword. The retained layer is the black moon-decorated sleeve tail ONLY, including its blue/gold pointed tip.
Keep the source's down-right sweep. One isolated clothing extension, no mannequin or new figure. Ideally keep the source's 1024x1536 canvas and original relative location.
TRUE transparent RGBA PNG. All outside pixels and cutout gaps fully transparent. No background, glow, fog, floor shadow, gradient, checkerboard, text or labels.
```

## leg_viewer_left

```text
Extract ONE single named animation layer from the attached approved chibi Jingliu illustration. Preserve the exact original pose, colors, Q proportions, dark-navy outlines and soft cel shading. No redesign.
True transparent RGBA PNG, ideally the same 1024x1536 canvas and original placement. All unrelated shapes removed to alpha zero. No backdrop, halo, gradient, fog, checkerboard, labels, character or additional objects. This is a clean 2D costume/animation asset extraction.
Retain ONLY the LEFT-SIDE LEG/BOOT in the picture (the one slightly farther back, with its boot tip ending higher than the right boot).
Keep its visible small section above the boot and its full ornate dark navy/blue boot, pale cuff and gold/silver decorations, same relaxed standing angle. Include only a short overlap at the upper edge so it can tuck under the front skirt; do not invent a whole upper body or reconstruct under clothing.
Delete the other leg and boot, all purple skirt, white front skirt, dark center garment panel, ribbons, arms, head, hair and weapon. One booted leg only. Preserve the slightly rearward orientation rather than mirroring the front leg. Original approximate visible area x260..449,y1072..1439. Whole boot including toe must be intact.
```

## leg_viewer_right

```text
Extract ONE single named animation layer from the attached approved chibi Jingliu illustration. Preserve the exact original pose, colors, Q proportions, dark-navy outlines and soft cel shading. No redesign.
True transparent RGBA PNG, ideally the same 1024x1536 canvas and original placement. All unrelated shapes removed to alpha zero. No backdrop, halo, gradient, fog, checkerboard, labels, character or additional objects. This is a clean 2D costume/animation asset extraction.
Retain ONLY the RIGHT-SIDE LEG/BOOT in the picture (the front/nearer one whose boot tip is lowest).
Keep its original visible section above the boot, pale cuff, ornate tall dark navy/blue boot, gold/silver edging and diamond/crystal-like motifs, original standing perspective. Include a small overlap at top to tuck below the skirt, no invented torso or hidden anatomy.
Remove the other booted leg and all fabric in front/behind it: no purple skirt, no white skirt, no central dark garment panel, no sleeve ribbon, no head/hair/arms or weapon.
Single booted leg only, preserve the low toe and original outline. Approximate source position x390..569,y1080..1525. Do not mirror, do not combine two feet.
```

## tassel

```text
Extract ONE single named animation layer from the attached approved chibi Jingliu illustration. Preserve the exact original pose, colors, Q proportions, dark-navy outlines and soft cel shading. No redesign.
True transparent RGBA PNG, ideally the same 1024x1536 canvas and original placement. All unrelated shapes removed to alpha zero. No backdrop, halo, gradient, fog, checkerboard, labels, character or additional objects. This is a clean 2D costume/animation asset extraction.
Retain ONLY the RED WAIST ORNAMENT / KNOT AND TASSEL from the source. It consists of the small red bow/knot, its short attachment loop, the small silver-white connector near the waist and the rounded curved red tassel pointing toward the right in the image.
Keep original red colors, white/silver connector, dark clean outlines and soft cel coloring. Complete only tiny areas obscured by adjacent garment edges.
Delete ALL blue/black/white/purple clothing, skin, arms, hair, other ornaments, sword and background. No extra hanging string, no long new tassel or invented symbol. This single small ornament lies roughly x467..640,y914..1036. A separate transparent accessory layer only.
```

