# 镜流分层抠图初版

本目录的 PNG 是单张部件图，不是序列帧。人物 10 层；两把独立武器位于 ../weapons/。

## 层级与归属

- head.png：脸、前发与脸侧短发、耳饰，作为完整头部。
- ponytail.png：单束高马尾与蓝色发带，跟随头部。
- torso.png：衣身与淡蓝前裙，已补画被手臂遮住的衣服。
- arm_viewer_left.png：画面左侧手臂，手部留出握持位置。
- arm_viewer_right.png：画面右侧弯曲手臂。
- skirt_back.png：紫色后裙摆，保持原紫色。
- sleeve_tail_viewer_right.png：黑色月相衣袖延伸，归属于画面右臂；不属于裙摆。
- leg_viewer_left.png、leg_viewer_right.png：两条独立腿靴。
- tassel.png：红色腰结与穗饰。

## 使用状态

均为 1024×1536 RGBA PNG，已检查 alpha 通道和透明区域，并在 ../parts_overview.png 中用透明网格实际排版查看。

部件包含 AI 辅助补画，并非无损像素复制。生成工具改变了部分部件在画布中的位置、大小，需要在动画绑定时按 alpha 包围盒缩放和校准。parts.json 记录的是建议父子关系、层级和源图锚点，尚无动画逻辑。

保持原始 PNG 不变。处理提示词和来源见上级目录的 PART_EDIT_PROMPTS.md 与 SOURCES.md。
