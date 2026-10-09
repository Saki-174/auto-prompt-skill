# 项目结构与模块关系

[文档导航](README.md) · [开发与验证](development.md) · [使用教程](usage.md)

## 实际目录树

下面按当前公开文件清单和实际存在的目录生成。所有列出的路径都存在；仅折叠被忽略的本地产物和缓存，不展开它们的内部内容。`.git/`是 Git 元数据，未列入源码树。默认构建输出`dist/`由构建命令创建，不是发布输入。

~~~text
auto-prompt-skill/
├── .agents/  # 插件目录发现；框架约定路径
│   └── plugins/
│       └── marketplace.json  # 仓库来源登记示例
├── .github/  # GitHub 自动检查
│   └── workflows/
│       └── ci.yml  # 单元、构建和 Windows 安装 CI
├── docs/  # 使用、维护、开发及证据导航
│   ├── history/  # 历史设计和证据；不作为当前能力声明
│   │   ├── git-history.md  # Git 对象映射与残留边界
│   │   ├── README.md  # 历史索引
│   │   ├── v1.0.1-design.md  # v1.0.1 设计取舍
│   │   └── validation-records.md  # 逐轮日期、基线、环境和结果
│   ├── releases/  # 各版本发布说明
│   │   ├── README.md  # 版本索引
│   │   ├── v1.0.1.md
│   │   ├── v1.0.2.md
│   │   ├── v1.1.0.md
│   │   └── v1.1.1.md
│   ├── chatgpt-acceptance.md  # 真实宿主来源与能力验收
│   ├── conversation-regression.md  # 12 项对话回归说明
│   ├── development.md  # 测试、构建与路径约定
│   ├── history-rewrite.md  # 旧公开路径兼容导航；正文已归档
│   ├── install.md  # 首次安装；保留旧维护锚点
│   ├── maintenance.md  # 升级、离线、恢复、卸载和手动路径
│   ├── migration.md  # 旧平台迁移范围
│   ├── project-structure.md  # 实际目录树、模块关系和路径对照
│   ├── prompt-quality.md  # 候选质量评估方法
│   ├── README.md  # 文档总入口
│   ├── release-v1.0.1.md  # 旧公开路径兼容导航；正文已归档
│   ├── release-v1.0.2.md  # 旧公开路径兼容导航；正文已归档
│   ├── release-v1.1.0.md  # 旧公开路径兼容导航；正文已归档
│   ├── release-v1.1.1.md  # 旧公开路径兼容导航；正文已归档
│   ├── runtime.md  # 调用流程、模型与脚本分工及质量边界
│   ├── security-maintenance.md  # ACL、输入保护、运行时及 CI 策略
│   ├── usage.md  # 输入、模式和生成后修订
│   ├── v1.0.1-design.md  # 旧公开路径兼容导航；正文已归档
│   └── validation.md  # 当前验证边界；保留历史锚点
├── examples/  # 三种合成严格 JSON 输入
│   ├── chatgpt.json
│   ├── codex.json
│   └── english.json
├── scripts/  # 安装、运行时准备和构建；生产逻辑只用标准库
│   ├── __pycache__/  # 本地产物／缓存，内部折叠；被忽略且不进入发布包
│   ├── build_release.py  # 三种 ZIP 和 SHA256SUMS
│   ├── install.py  # 受管文件、登记、事务及恢复
│   ├── install_permissions.py  # Windows 安全描述符／POSIX mode 辅助
│   ├── legacy-v1.0.0.json  # 无管理清单的旧版文件摘要基线
│   ├── package-files.json  # 技能与整合包公开文件白名单
│   ├── runtime-lock.json  # 固定官方运行时坐标与摘要
│   └── runtime.ps1  # 解释器探测、下载校验与准备锁
├── skills/  # 宿主发现目录；保持固定结构
│   └── auto-prompt/  # 实际可安装技能
│       ├── agents/  # 宿主发现元数据
│       │   └── openai.yaml
│       ├── references/  # 输入、交互和改编来源
│       │   ├── conversation.md
│       │   ├── grill-me-attribution.md
│       │   └── input.md
│       ├── scripts/  # 严格执行入口与维护策略
│       │   ├── render_prompt.py
│       │   ├── Run-Strict.ps1
│       │   └── runtime_policy.py
│       ├── templates/  # 中／英文 × 开发／通用，共四套模板
│       │   ├── en-development.txt
│       │   ├── en-general.txt
│       │   ├── zh-development.txt
│       │   └── zh-general.txt
│       ├── LICENSE
│       ├── NOTICE
│       └── SKILL.md  # 宿主执行规则和模式分流
├── tests/  # 开发和发布验证；不属于安装后的技能程序
│   ├── fixtures/  # 旧输出与合成对话／质量样例
│   │   ├── conversations.json
│   │   ├── legacy.json
│   │   └── prompt-quality.json
│   ├── test_install_permissions.py
│   ├── test_install_recovery.py
│   ├── test_install_release.py
│   ├── test_install_upgrade.py
│   ├── test_maintenance_contract.py
│   ├── test_render_prompt.py
│   ├── test_security_regressions.py
│   ├── test_windows_runtime.py
│   └── windows_acceptance.ps1  # 隔离 Windows 安装和恢复集成
├── .gitattributes  # 文本属性
├── .gitignore  # 排除本地产物与敏感文件
├── Install-Windows.cmd  # Windows 双击安装入口
├── Install-Windows.ps1  # 依赖准备、安装和自检入口
├── LICENSE  # 项目 ISC 许可
├── NOTICE  # 第三方来源说明
├── plugin.json  # 插件身份、版本及技能路径
├── README.en.md  # 英文首页
├── README.md  # 中文首页与快速入口
└── work/  # 本地产物／缓存，内部折叠；被忽略且不进入发布包
~~~

## 主要使用路径

| 场景 | 入口及模块关系 |
| --- | --- |
| 网页个人导入 | 插件 ZIP → 宿主导入插件清单 → 技能入口及参考文件；云端执行能力单独检查 |
| Windows 本地安装 | Install-Windows.cmd → Install-Windows.ps1 → scripts/runtime.ps1 → scripts/install.py |
| 权限与事务 | install.py 动态加载 install_permissions.py；旧安装按 legacy-v1.0.0.json 识别，当前安装写管理清单 |
| 灵活转换 | 宿主读取 SKILL.md、交互和输入参考，再由当前模型生成；本项目没有模型 API 客户端 |
| 严格转换 | Run-Strict.ps1 检查登记运行时，调用原维护策略和 render_prompt.py；渲染器选择四套模板之一 |
| 打包 | build_release.py 读取 package-files.json 和 plugin.json，生成三个 ZIP 及校验清单 |
| 自动检查 | CI 调用 tests/ 和构建入口；Windows 集成使用隔离目标目录 |

运行规则随技能安装；仓库指南面向使用者和维护者，不会全部成为宿主默认输入。模型、技能规则与严格脚本的具体分工见[运行逻辑](runtime.md)。

## 源码、安装与发布包

| 内容 | 用途 |
| --- | --- |
| 源码仓库 | 实现、配置、文档、合成样例、测试和构建入口 |
| 整合包 | 白名单中的完整本地安装与开发检查材料；不含解释器 |
| 插件包 | 根插件清单、许可和来源说明，加技能白名单文件 |
| 单技能包 | 技能白名单文件，以 auto-prompt/ 为包根目录 |
| 本地安装结果 | 仅复制技能程序；插件模式再添加插件清单、许可和来源说明，并生成安装归属清单 |
| work/、缓存和构建目录 | 本地工作／生成产物；不作为发布输入，不自动清理 |

Windows 运行时需要时从固定官方来源另外准备，保留原许可；第三方下载内容不手工重排。技能内重复携带许可是独立分发需要，不应当作无用副本。

## 本轮路径调整与回滚

| 旧路径／内容 | 新路径 | 兼容处理 |
| --- | --- | --- |
| `docs/release-v1.0.1.md` | `docs/releases/v1.0.1.md` | 正文归档，旧路径保留章节导航 |
| `docs/release-v1.0.2.md` | `docs/releases/v1.0.2.md` | 正文归档，旧路径保留章节导航 |
| `docs/release-v1.1.0.md` | `docs/releases/v1.1.0.md` | 正文归档，旧路径保留章节导航 |
| `docs/release-v1.1.1.md` | `docs/releases/v1.1.1.md` | 正文归档，旧路径保留章节导航 |
| `docs/v1.0.1-design.md` | `docs/history/v1.0.1-design.md` | 正文归档，旧路径保留章节导航 |
| `docs/history-rewrite.md` | `docs/history/git-history.md` | 正文归档，旧路径保留章节导航 |
| `docs/install.md` 的维护章节 | `docs/maintenance.md` | 首次安装仍在原路径；旧章节链接保留 |
| `docs/validation.md` 的逐轮历史记录 | `docs/history/validation-records.md` | 当前边界仍在原路径；历史锚点保留 |

新增文档导航、使用、开发和结构说明；技能自动发现目录、安装／CLI 入口、源码模块、测试路径、模板及版本保持不变。发布白名单保留旧导航页并加入新正文，避免离线包内断链。

需要回滚时先保留当前修改：按表把正文移回原位置，删除对应兼容导航，并只撤销本轮引用调整和新增白名单条目。合并回来的正文必须保留之后的用户修改；不要用旧备份整文件覆盖已有改动，也不要全局重置。此前已有的质量文档、用例和导航条目不属于可直接删除的本轮新增内容。

## 文档职责

首次操作查安装和使用；后续问题查维护。开发和测试查开发说明，当前证据查验证说明。发布说明按版本维护，历史记录保留其原时点。旧导航页只维护跳转，不复制正文。
