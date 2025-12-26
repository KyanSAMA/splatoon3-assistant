# 数据层

该目录集中存放所有静态数据资产，供前端直接消费或由后端注入 SQLite。

| 目录 | 内容 |
| --- | --- |
| `json/` | 原始 JSON 语料（武器参数、技能描述、API mock、打工日程等） |
| `images/` | 已整理好的素材：`weapon/`、`subWeapon/`、`specialWeapon/`、`stage/` 等 |
| `langs/` | 多语言文本资源，`zh-CN` 下含武器、阶段、系统提示等翻译 |
| `docs/` | 深度资料（机制解析、武器攻略等文字内容） |

## 使用方式

- 后端脚本 (`../backend/scripts`) 会从 `json/` 读取参数，再写入 SQLite。
- 前端可直接 fetch `json/` 文件，实现完全静态的数据展示。
- 如需扩展，建议在 `data/json` 下按主题拆分新的子目录，并同步更新相应 README。
