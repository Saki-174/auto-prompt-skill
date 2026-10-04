# 验证

运行：

```sh
python -m unittest discover -s tests -v
python scripts/build_release.py
```

`tests/fixtures/legacy.json` 包含直接由旧 TypeScript 渲染器产生的 32 组 UTF-8 SHA-256 基线，覆盖中英文、两个 profile、缺失／不同 Agent、CRLF、多行约束、emoji 和原始占位符。测试比较完整输出摘要，不仅检查标题。

其他验证覆盖：

- 空需求、错误类型、未知字段、重复键、长度和不支持的语言报错。
- 原文与占位符原样保留、相同输入结果一致、严格模式不调用模型。
- JSON CLI、标准输入、从不同工作目录运行、保护原始输入文件。
- 安装器保留原有插件条目、更新备份、重复安装不重复登记、来源冲突不修改配置。
- ZIP 路径和结构、同源可复现打包、校验值，不纳入私有运行文件。

脚本测试不能证明模型自动选择技能的准确率，也不能证明某账号的 ChatGPT 插件安装入口可用。安装后还需在新对话进行以下手动验收：

| 输入 | 预期 |
| --- | --- |
| 调用 Auto Prompt：Codex＋Unity 对象池＋禁止新增依赖 | 生成提示词，保留约束，不编造版本、规模或 API，不执行开发 |
| 调用 Auto Prompt：ChatGPT Work＋已提供的会议记录整理需求 | 通用模板，缺失信息待确认，不声称读取未提供文件 |
| 提供完整 JSON，并连续运行两次 | 严格结果一致，脚本输出未经模型改写 |
| 显式 strictMode=false，要求自然表达 | 当前模型灵活整理，未调用旧后端 |
| 调用 Auto Prompt，未指定 Agent | Agent 为待确认，不默认选 Codex |
| 未调用技能，直接要求实现对象池 | 不因提到 Agent 或软件开发就误用提示词转换技能 |
| 主机无法运行 Python | 明确说明规则生成限制，不声称已运行严格脚本 |

GitHub CI 用 Windows／Linux × Python 3.9／3.12 执行测试。某次 CI 是否通过，以该次 Actions 记录为准。
