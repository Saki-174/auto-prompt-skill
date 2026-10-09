# 开发与验证

[文档导航](README.md) · [项目结构](project-structure.md) · [验证边界](validation.md)

## 环境与操作位置

以下命令在源码仓库或完整整合包的根目录运行，确认能看到`plugin.json`、`scripts/`、`skills/`和`tests/`。使用符合[维护策略](security-maintenance.md#运行时维护)的 Python；生产脚本仅用标准库，不需要安装 pip 依赖。

Windows 自动运行时准备仅支持 x64。本地测试不能代替 Linux、其他 Python 或宿主对话验收；实际环境和跳过项必须记录。

## 自动测试与构建

在上述根目录的终端运行：

~~~sh
python -m unittest discover -s tests -v
python scripts/build_release.py
~~~

第一条正常结果是 unittest 汇总，无失败；跳过项记录原因。第二条生成三个 ZIP 和`SHA256SUMS.txt`到`dist/`，文件名由`plugin.json`的版本决定。构建不会创建标签或上传发布附件。

如需把候选产物放在其他位置：

~~~sh
python scripts/build_release.py --output work/candidate
~~~

`dist/`与`work/`被忽略，不属于分发输入。构建只接受[scripts/package-files.json](../scripts/package-files.json)列出的安全来源；单技能包、插件包和整合包用途见[项目结构](project-structure.md#源码安装与发布包)。检查白名单、CRC、校验清单、逐文件内容和重复构建一致性，不能仅确认 ZIP 可打开。

## Windows 安装集成

在 Windows 仓库根目录的 PowerShell 中运行下面的离线示例，替换全部示例路径；输出目录使用专属的新目录，不指向真实用户配置：

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\windows_acceptance.ps1 -RuntimeArchive 'C:\downloads\python-3.13.16-embed-amd64.zip' -RecentBundle 'C:\downloads\auto-prompt-skill-1.0.2-bundle.zip' -OutputDirectory 'C:\temporary\auto-prompt-evidence'
~~~

`RuntimeArchive`必须是与锁定摘要一致的官方 ZIP。`RecentBundle`必须是验收脚本支持的正式 v1.0.2 包；`LegacyBundle`对应 v1.0.0，`PreviousBundle`对应 v1.0.1，可按需另外传入。未提供的旧版本路径不会执行；不能互换参数或放宽固定摘要。`AllowDownload`允许实际联网准备运行时，此时不需要提供离线 ZIP。

脚本用隔离的目标用户目录检查依赖准备、严格自检、重复安装、升级、恢复、并发准备和全局 PATH。正常结果包含检查汇总文件`windows-acceptance.json`；实际检查数随参数和平台而变，不预填通过。测试目录并非干净虚拟机；权限、系统组件和宿主登录仍来自当前机器。

## 对话与生成质量

- [宿主验收](chatgpt-acceptance.md)：加载来源、版本、工具、运行时和严格执行证据。
- [对话回归](conversation-regression.md)：引导、权限边界、跨任务隔离、追加／替换／撤销。
- [质量对照](prompt-quality.md)：保真通过后比较清晰度、领域适配和信息密度。

用例 JSON 可解析不代表模型通过；只给被测模型输入，不给预期答案。原始日志和账号信息留在私有目录，公开记录只保留必要的脱敏结果。

## 路径与维护约定

`Install-Windows.cmd`、`Install-Windows.ps1`、`plugin.json`和技能自动发现目录保留公开路径。安装器、运行时助手和测试依赖相对目录关系，不应只移动某个脚本。涉及路径调整时同步检查 import、资源、白名单、CI、示例和文档链接。

Windows ACL 事务模块、旧版文件摘要、许可证和来源说明都有实际用途。不要因未被普通聊天直接读取而删除。历史设计和验收在`docs/history/`，各版本发布说明在`docs/releases/`；旧文档路径仅保留兼容导航，不重复维护正文。

## 发布与回滚边界

完整流程见[验证说明](validation.md#发布门槛)。源码修改、候选构建、Git 提交、GitHub 发布和客户端刷新是独立操作；构建成功不授予后续发布权限。

结构调整的路径对照与回滚方法见[项目结构](project-structure.md#本轮路径调整与回滚)。仅撤销本阶段改动；保留已有用户修改，不全局重置或删除整个配置目录。
