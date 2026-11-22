# 版本记录

格式遵循 Keep a Changelog。版本规则见 `AGENTS.md`。

## v0.6.0 — 2026-11-23

- 仓库可见性由私有改为公开，用于一起学习和交流。
- README 新增「学习交流」章节，公开微信群二维码，注明有效期与更新方式。
- 新增配图 `docs/community/wechat-group-qr.png`。`.gitignore` 精确放行该图。

## v0.5.0 — 2026-11-23

- 新增课程讲义类文档：`docs/course/ten-lectures-outline.md`。三段 10 讲的目标、内容、时间估算、每讲节奏与验收标准。
- 新增课程讲义类文档：`docs/course/lecture-0-llm-call.md`。裸调用与 Agent 循环的差别、`messages` 角色、`tool_calls` 结构化文本、可运行请求脚本与小测。
- 新增配套配图：`docs/course/ten-lectures-outline.png`、`docs/course/lecture-0-call-vs-loop.png`。
- `README.md` 资料范围与索引新增课程讲义条目。`AGENTS.md` 补入课程讲义目录映射。`.gitignore` 精确放行两张配图。

## v0.4.1 — 2026-11-22

- 替换 `docs/product/module-fishbone-diagram.png` 为六根骨齐全的版本。
- 移除文档中关于下方三根骨标签被裁切的说明。

## v0.4.0 — 2026-11-22

- 新增子模块索引类文档：`docs/product/module-fishbone.md`。按六个用户能力域划分功能，标注机制锚点与挂靠功能、复用机制和源码位置。
- 新增配套配图：`docs/product/module-fishbone-diagram.png`。
- README 资料范围与索引新增子模块索引条目。

## v0.3.1 — 2026-11-22

- 更新 `AGENTS.md`：目录映射补入技术架构类，明确脱敏技术示意图可作为配图入库。
- 更新 `.gitignore`：精确放行技术架构配图。

## v0.3.0 — 2026-11-22

- 新增技术架构类文档：`docs/code/architecture-source-mapping.md`。逐层记录五层架构与源码文件行号的对应，含三条不变量、版本漂移表和复现命令。
- 新增配套配图：`docs/code/architecture-layers.png`。
- README 资料范围与索引新增技术架构条目。

## v0.2.1 — 2026-11-22

- README 资料索引只保留已入库文档，移除未入库资料的登记条目。

## v0.2.0 — 2026-11-22

- 在 `README.md` 新增资料索引，按主题分组登记全部学习资料。已入库项给链接，未入库项标注状态与用途。
- 新增证据基线速查表，列明界面版本与两条源码分析基线。

## v0.1.0 — 2026-11-22

初始版本。

- 新增产品功能地图脱敏版：`docs/product/feature-map.md`。
- 新增源码基线与复现记录：`meta/sources.md`。
- 新增同步与版本管理约定：`AGENTS.md`。
