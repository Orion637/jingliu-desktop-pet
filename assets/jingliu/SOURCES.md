# 镜流 Q版桌宠素材记录

## 当前采用素材

- 文件：processed/jingliu_cutout_refined_high_ponytail.png
- 内容：单张透明 RGBA PNG，1024 × 1536；高马尾修订版。
- 当前阶段：原画抠图、边缘补全与精修；已拆出 10 个人物部件，另保留两种独立武器。部件尚需绑定前的位置与转轴校准，未制作动画、桌宠程序、HID 或 DSH 功能。

## 原始底图

- 作者：久方 🧪 / @Range0v0。
- 作品：鏡流 #崩壊スターレイル，2023-08-02。
- 页面：https://twiman.net/user/264722798/illust/1686701885397549061
- 原图：https://pbs.twimg.com/media/F2hebINa4AAQjna.jpg
- 原图本地保留：original/jingliu_range0v0.jpg，未覆盖。
- 原作者作品未查到开放改绘许可证；不能将该原画或本次加工结果标注为 MIT、CC0 或自行拥有的原创角色作品。本次按用户指定的个人本地用途加工，保留署名、来源，不据此推定有公开再分发或商业授权。

## 细节参考

以下资料在 Honkai: Star Rail Wiki 的 Jingliu/Media 页面标注为官方设定/游戏素材；本次通过其图集取得，只作为造型参考，未引入 3D 模型或 SDK。

- 汇总页面：https://honkai-star-rail.fandom.com/wiki/Jingliu/Media
- references/official_reference_1.webp：角色前、侧、背多视设定，以及护臂、发型和服饰细节。
  - https://honkai-star-rail.fandom.com/wiki/File:Character_Reference_Sheet_Jingliu_1.jpg
  - https://static.wikia.nocookie.net/houkai-star-rail/images/0/00/Character_Reference_Sheet_Jingliu_1.jpg/revision/latest?cb=20260604001959
- references/official_reference_2.webp：仅取上半部分镜流武器和小型立绘参考。下半部分是白珩，不属于镜流，本次明确排除。
  - https://honkai-star-rail.fandom.com/wiki/File:Character_Reference_Sheet_Jingliu_2.jpg
  - https://static.wikia.nocookie.net/houkai-star-rail/images/b/bb/Character_Reference_Sheet_Jingliu_2.jpg/revision/latest?cb=20260604002004
- references/official_portrait.webp：镜流游戏立绘。
  - https://honkai-star-rail.fandom.com/wiki/File:Character_Jingliu_Portrait.png
  - https://static.wikia.nocookie.net/houkai-star-rail/images/e/ea/Character_Jingliu_Portrait.png/revision/latest?cb=20231012130908
- 角色与官方素材相关权利归 miHoYo / HoYoverse 等相应权利人所有。Wiki 的页面许可不视为第三方图像的统一开放许可。

## 加工方式与修订

- 使用 Codex 内置 image_gen 图像编辑工具，transparent_background=true；未使用 CLI/API 回退。
- v1：保留 Q版脸型、红眼、姿势和短冰剑，补齐头顶、发梢、飘带、鞋尖，清理背景与矩形画框，精修衣饰。
- v2：按用户明确修正，后发改为单束高马尾，保留蓝发带、前刘海、脸侧碎发与原有神态。
- 最终图是 AI 辅助恢复、修整后的版本，不是纯像素无损抠图，补全细节含推断。
- PNG 透明度需以文件 alpha 通道为准；部分预览器可能显示完全透明像素内保留的背景 RGB。
- 完整提示词见 EDIT_PROMPTS.md。

## 独立武器与 Q版统一修订

- 用户要求：武器设定图里的两种剑形都要制作，随后要求画风与 Q版人物更搭配。
- weapons/sword_slender_chibi.png：设定图左侧细剑的 Q版化独立透明 PNG。
- weapons/sword_ice_chibi.png：设定图中间宽刃冰剑的 Q版化独立透明 PNG，保留开放式菱形护手与中央冰晶。
- 相比最初道具稿，统一使用粗深蓝轮廓、减少细碎切面、扩大明暗色块和护手可读性，并调整为较紧凑的插画比例。
- 两个独立道具仍属于 AI 辅助参考重绘，存在造型推断，不声称与官方贴图逐像素一致。
- 完整角色合成图仍保留；parts/ 中提供独立部件。武器尚未绑定到可切换的手部图层，运行时动画尚未制作。
- 初次细剑生成遇到图像工具 violence 分类拦截；以无人物、无使用场景的静态幻想道具图明确用途后重试成功。
- 验证记录：asset_validation.json，检查 PNG 解码、RGBA alpha 范围及文件 SHA-256。

## 部件拆分与用户结构修正

- 10 个人物部件：头部（含前发）、单束高马尾、衣身与前裙、画面左臂、画面右臂、紫色后裙摆、右袖黑色月相延伸、左腿靴、右腿靴、红色腰穗。
- 用户最终决定：不改变颜色，紫色裙摆保持原色。
- 黑色月相飘带属于画面右侧手臂的衣袖延伸，parts/parts.json 将其 parent 设为 arm_viewer_right；不得和裙摆合成一个部件。
- 最初将二者合并的后摆草稿已弃用，未列入部件清单及交付包。
- 生成工具完成部件提取及遮挡补全；只读像素检查用于验证透明度。parts_overview.png 是将原部件在网格上排版的静态检查图，没有再次生图或重绘部件。
- 部件的原始画布均为 1024×1536，但提取工具会改变可见部件的大小和位置。parts/parts.json 的锚点和范围是源图坐标的建议值，不表示已完成精确对齐；绑定前应依据 alpha 包围盒校准。
- 部件验证：parts/validation.json；提示词：PART_EDIT_PROMPTS.md。


