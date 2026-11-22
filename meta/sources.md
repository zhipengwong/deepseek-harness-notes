# 源码基线与复现

本库不存上游源码。本文件记录研究时对应的版本，供复查使用。

## 上游仓库

- 地址：`https://github.com/deepseek-ai/deepseek-harness`
- 说明：基于 Cordis 的插件化 Agent 框架，官方开发者预览版。
- 复现命令：

```
git clone https://github.com/deepseek-ai/deepseek-harness.git
git -C deepseek-harness rev-parse HEAD
```

## 研究基线

| 标记 | commit | 版本 | 用途 |
|---|---|---|---|
| 界面截图 | 无对应 commit | `0.2.2-rc.5` | 功能地图的界面事实来源 |
| 分析基线 A | `fcc0ad4` | `0.2.2-rc.1` | 早期架构研究 |
| 分析基线 B | `4b399c39a6d1479cd84ca591b4d7c88e24d38a96` | `0.2.3-alpha.2` | 当前代码研究 |

界面版本卡在两条分析基线之间。任何界面字段到源码行号的映射，先 checkout 与 `0.2.2-rc.5` 对应的 commit。

## API 一手资料

- 文档首页：`https://api-docs.deepseek.com/zh-cn/`
- 工具调用：`https://api-docs.deepseek.com/zh-cn/guides/tool_calls`
- 上下文硬盘缓存：`https://api-docs.deepseek.com/zh-cn/guides/kv_cache`

API 层结论来自上述官方文档。仓库内文档引用这些结论时，注明来自一手文档。
