# 迁移范围

v1.0.1 面向 ChatGPT 本地宿主，目标 Agent 可以不同。自然语言默认改为灵活模式；完整旧 JSON 和直接严格 CLI 的默认行为保持。安装升级规则和可恢复事务见 [安装说明](install.md)。

本版本迁移的是“Agent＋原始需求 → 规范提示词”工作流。`prompt-mcp-adapter` 的旧版严格模式与模板是兼容基线，不迁移完整的原 Auto Prompt Web 平台。

| 旧能力／组件 | 新版本 |
| --- | --- |
| 目标、约束、上下文、交付物识别 | Skill 由当前模型完成 |
| Agent 适配、禁止编造、缺失信息 | Skill；严格模板保留旧行为 |
| strictMode 确定性拼接 | 标准库 Python＋四个模板文件 |
| development／general、中英文 | 保留，旧版 CLI 默认 development／中文 |
| optimize_prompt 的 JSON 输入及输出 | 核心字段兼容；`--format json` 返回 optimizedPrompt 与 model |
| Ollama／外部模型优化 | 不迁入；灵活模式使用当前模型 |
| enableDeepReasoning | 严格模式兼容接收但无效果；不启动外部推理 |
| MCP Adapter／Tunnel／启动任务 | 新版本不依赖；未自动停止或删除 |
| 原平台界面、账号、历史库、评测、图片优化 | 不包含 |
| CYX-MEMORY | 独立项目，不属于本迁移 |

严格模式原样保留原始需求，不自动补齐上下文、不翻译需求、不选择具体技术实现。脚本验证比旧函数更显式：拒绝未知字段、重复 JSON 键、错误类型及混合 CLI 输入；保留旧 MCP 的输入长度限制。

语言检测沿用旧实现，不是全面语义识别。例如 requirements 中提及英文就会触发英文标题；不适合将与输出语言无关的长背景放进该字段。使用 JSON 时建议明确、简短地表达输出语言；灵活模式能按语义处理这些区别。

兼容基线：本地 adapter commit `d77c102` 的 `src/strictPrompt.ts`。文件 SHA-256：`b2d90f4a97ee7f8ba145dfc00bdad0f956c7b6ce44cd6201a68a0df1841dffff`。公开测试向量全部为合成需求，不含用户项目资料。

## 旧部署的保留与停用

迁移不需要导出旧 `.env`、运行密钥、数据库或 Tunnel 标识。源码包通过白名单构建，只发布新 Skill 工作流所需文件。

先在新对话使用几条真实需求检查结果。若之后决定停用旧部署，应确认 Auto Prompt 专用启动任务、Adapter 进程、Tunnel 和 Docker 项目确属专用；CYX-MEMORY 与其他程序可能使用自己的 Tunnel、Docker 或 Ollama。只有完成这种检查后才单独停用 Auto Prompt 的部分。不要卸载整个 Docker／Ollama，也不要删除共享模型或数据卷来完成本迁移。

本仓库不包含自动停止旧部署的脚本，避免把通用安装流程绑定到某台电脑的服务结构。
