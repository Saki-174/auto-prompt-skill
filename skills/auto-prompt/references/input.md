# 输入与确定性边界

```json
{
  "targetAgent": "Codex",
  "rawPrompt": "帮我写一个 Unity 对象池。",
  "requirements": "只允许修改 Assets/Scripts。不要新增依赖。",
  "profile": "development",
  "strictMode": true
}
```

| 字段 | 必须 | 默认与限制 |
| --- | --- | --- |
| rawPrompt | 是 | 非空字符串；去除首尾空白后最多 20000 个 UTF-16 单位 |
| targetAgent | 否 | 字符串、单行；未提供或空白写“待确认”；连续空白合并 |
| requirements | 否 | 字符串，默认空；最多 8000 个 UTF-16 单位 |
| profile | 否 | development 或 general；CLI 默认 development |
| strictMode | 否 | 默认 true；脚本只接受 true，false 由当前模型灵活生成 |
| enableDeepReasoning | 否 | 兼容旧输入的布尔值；严格模式忽略此值，不调用模型 |

脚本拒绝未知字段、重复 JSON 键和错误类型，避免悄悄丢掉用户约束。没有从旧项目迁移任何环境变量或认证信息。

严格模式语言判断保留旧版行为：requirements 中出现 english、英语、英文则用英文标题；否则默认中文。只改变模板语言，不翻译 rawPrompt 或 requirements。旧版检测到的其他显式语言会报错；其检测规则不是完整语言分类器。请把实际输出语言明确放到 requirements，不把无关语言描述放入该字段。

默认补入中文、缺失信息待确认、禁止虚构规则；已有对应约束时不重复补入。具体实现、数字、路径和占位符只来自用户输入，模板本身不选择它们。

`--format json` 返回旧 API 风格的 `optimizedPrompt` 与 `model: strict-deterministic-v1`。这是外层序列化格式，requirements 内“输出 JSON”这类文字仍保留为目标任务的要求，不自动解释成当前转换器的 CLI 参数。

严格渲染不是对全文的矛盾检测。明确约束与固定模板不兼容时，先说明冲突；不要承诺严格模式已解决语义问题。灵活模式可按用户格式重写，但不能保证字节一致。
