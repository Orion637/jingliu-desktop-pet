# 镜流 · 二维骨骼桌宠整合版

镜流二维骨骼桌宠 v1.1，支持 14 个动作、双武器切换、透明桌面窗口、全屏自动隐藏及设备 / DSH 状态面板。

Windows 免安装包与完整源码包见 [Releases](../../releases/latest)。下载 Windows 包后完整解压，双击 `JingliuPet.exe`；请保留 `_internal` 文件夹。源码运行方法见下方。

## 使用

- 预览窗口：点击右侧动作名称；可切换细剑 / 宽刃冰剑 / 空手，显示骨骼，暂停和重播。
- 「放到桌面」：显示透明、无边框、置顶桌宠。
- 单击人物：随机播放歪头、摸头、招手、点头、摇头、小跳、细剑致意、冰剑展示或月弧挽剑；连续点击不重复上一个动作，结束后回到待机。
- 左键按住拖动：手脚晃动；松开回到待机。少量鼠标移动不会误触拖拽。
- 右键：动作、武器、大小、暂停、退出。
- 双击桌宠或托盘：打开动作预览。关闭预览后，已显示的桌宠继续运行。
- 退出请用右键「退出镜流」。未显示桌宠时关闭预览也会退出。
- 全屏时自动隐藏：默认开启，退出全屏自动恢复；右键可关闭。普通最大化窗口不隐藏，全屏时关闭动作预览也不会退出桌宠。

重复启动会唤回已有窗口；同一安装目录只保留一个实例。

## 设备与 DSH

点击桌宠底部角标或右键「设备电量 / DSH 状态」，查看 ROG 棱镜 2 电量、G3M 状态、DSH 轮次/Token 和 DeepSeek 官方余额。「数据源设置」可修改 DSH 路径及配置安全保存的 API Key。

G3M Pro 2.4G 已支持 Telink 320F:706E，需切到 2.4G 并唤醒鼠标。设备未连接或未响应时显示 N/A。新面板使用蓝紫色卡片、大号电量和电量条。DSH 未运行时隐藏其进度区域。后台读取各自隔离、有超时，退出会清理。余额约 60 秒缓存。详见 [完整使用说明](docs/integration-guide.md)。

## 已制作的动作

待机呼吸浮动、左右环顾、点击歪头、摸头摇晃、招手、点头、摇头、小跳、拖拽晃动、歪头休息、细剑致意、冰剑展示、眨眼、月弧挽剑，共 14 个动作。招手、拖拽、休息时暂时收起武器，结束后恢复所选武器；细剑/冰剑展示会切换到对应武器。另有定时自动眨眼。

切换武器可用选择框、「切换武器 · 冰霜凝刃」按钮或右键菜单。旧剑先化为霜粒，新剑从柄向剑尖凝成，期间握点跟随手掌。手指在剑柄前方单独遮挡；剑柄比例收紧。月相飘带起点藏在右袖后方，末端有延迟摆动。特效为实时矢量绘制。

眨眼由眼部遮罩、眼睑覆盖和连续压缩驱动，发丝遮挡保持在上层；头部原 PNG 保留。目前没有口型；四肢使用整块部件，当前没有拆肘部/膝部。

## 绑定结构

`assets/jingliu/rig.json`：18 个骨骼、部件对齐、关节位置、图层、武器握点、网格权重。颈部连接藏于下巴和高领下方，按原图保持紧凑衔接；右肩按衣身重新对齐。

`assets/jingliu/animations.json`：14 组关键帧。平滑插值和 0.24 秒动作过渡由纯 Python 核心执行。马尾、袖带、后裙及隐藏颈部连接使用带权重网格；其余部件刚性跟随骨骼。高马尾跟头部，黑色月相袖带跟右臂，紫色裙摆跟身体。两把武器跟画面左手握点，并以运行时网格收紧剑柄。

所有原始 PNG 保留。运行时按 alpha 包围盒取图并在内存中绘制，动画不播放 PNG 序列。GIF/MP4 仅供查看，运行程序不读取这些演示文件。

## 工程入口

```text
core/                  纯 Python：FK、仿射变换、权重、关键帧与动作过渡
ui/                    PySide6：绘制、动作面板、透明窗口、托盘和交互
assets/jingliu/         原图、分件、武器、rig.json、animations.json
tools/                 动作数据制作和预览导出
tests/                 数学与交互回归检查
preview/               总览、绑定图、GIF 和 MP4
qa/                    渲染统计、源图哈希与检查记录
logs/jingliu.log        本地启动日志
```

`sources/` 提供独立的 HID、DSH、余额读取；`ui/sources.py` 管理后台读取进程。DSH 原日志始终只读。

## 开发和重新安装

已在 Windows / Python 3.12.14 / PySide6 6.8.3 下验证。本机 `.venv` 供本机使用，不建议复制虚拟环境到其他电脑。新电脑先安装 Python 3.12，然后在项目目录执行：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py --preview
```

检查与导出：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py --smoke-test
.\.venv\Scripts\python.exe tools\export_preview.py
```

`tools/build_animation_data.py` 是 JSON 的制作脚本。手动修改 JSON 后不要随意重新运行它，因为它会重新写入默认绑定和动作数据。

## 来源

人物原画、角色和参考图来源见 [素材来源](assets/jingliu/SOURCES.md)，分件和武器的处理记录也保留在素材目录。现有同人图未核实为开源授权素材，不能将整个素材包标为 MIT / CC0。

应用逻辑为本项目编写。运行库的许可证保留在 `.venv/Lib/site-packages`；Qt/PySide6 使用其 LGPL/GPL/商业许可体系，Pillow 和 imageio-ffmpeg 使用各自许可证。导出的 FFmpeg 日志位于 `qa/ffmpeg.log`。

Qt 绘制和托盘 API 查阅：[QPainter 官方文档](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPainter.html)、[QSystemTrayIcon 官方文档](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSystemTrayIcon.html)。
