# 验证与证据范围

## 自动化

~~~sh
python -m unittest discover -s tests -v
python scripts/build_release.py
~~~

保留 32 组旧严格输出摘要，以及 CLI、输入边界和原文保留检查。新增安装事务测试包括：独立用户文件与其他目录条目保留、管理文件冲突、路径冲突、重复安装、目录/运行时写入失败恢复、完整/中断事务回滚、后续编辑保护、备份篡改拒绝、重复 JSON、并发锁、链接路径拒绝和 Python 能力检查。

打包使用 scripts/package-files.json 的精确白名单，构建两遍核对字节重现性；不打入解释器、配置、机器日志、备份或源码目录外文件。

## Windows 集成验收

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\windows_acceptance.ps1 -RuntimeArchive 'C:\downloads\python-3.13.12-embed-amd64.zip' -LegacyBundle 'C:\downloads\auto-prompt-skill-1.0.0-bundle.zip' -OutputDirectory 'C:\temporary\auto-prompt-evidence'
~~~

也可用 -AllowDownload 走实际官方下载路径。显式使用隔离的空用户根目录和 -DedicatedRuntime，防止测试意外复用开发机的全局 Python。测试覆盖离线首次准备、运行严格脚本、重装复用、兼容/不兼容解释器处理、损坏 ZIP、v1.0.0 升级与回滚，以及全局 PATH 不变。

该测试只模拟空目标用户目录，不等同于干净 Windows 虚拟机；系统组件、权限、杀毒软件和宿主登录仍来自实际机器。Python/PowerShell/OS 版本和实际测试结果应记录在本地交付报告中；未运行的平台明确留待验证。

现有 CI 矩阵保留 Windows/Linux × Python 3.9/3.12。发布需等待当前提交对应的四组检查通过，不把历史版本 CI 结果当作当前提交证据。

## 真实 ChatGPT 验收

按 [新对话清单](chatgpt-acceptance.md)执行。引导问句是否合适、是否出现真实提示框、自然语言跨领域质量以及用户回答后的处理，均不能靠脚本或字符串断言认定通过。观察实际工具调用和新版本路径，避免模型口头声称使用了新技能。

## 发布门槛

实现与自动检查完成后，只生成本地候选包和摘要。用户本地验证通过且明确批准后，才能考虑提交/推送、标签、Release 或上传发布附件。本项目通过 GitHub Release 分发，没有进入公共插件目录。

## v1.0.1 本机验收结果（2026-10-05）

- Windows x64、Windows PowerShell 5.1；Python 3.12.14 与 3.13.12 各 23 项测试通过，包含 32 组旧输出比对。
- 隔离空用户环境的运行时准备、真实官方下载、兼容解释器复用、损坏包拒绝、旧版升级和恢复检查通过；最终候选包的 24 项 Windows 集成检查通过。
- 真实用户目录由 1.0.0 升级至 1.0.1，重复安装无变化，备份与原文件逐字节一致，官方插件刷新后新对话实际读取 1.0.1。
- 用户确认的 ChatGPT 本地 Work 会话中，空调用引导、真实结构化提问、视频需求澄清、未知项停止追问、来源约束冲突以及开发/学习/研究/写作提示词生成通过。
- Work 新对话实际执行严格脚本两次，均退出 0、输出 1296 字节，SHA-256 为 `650b898d02661131657e3d3f502c7bf9d0e3c0ce1f47bca85257e76d725e52d2`；返回正文与文件一致。独立新聊天的旧 JSON 缺省 strictMode 用例同样通过。
- 用户完成本地验收并明确批准发布。界面模式依据用户确认；本机执行路径和调用记录已检查。公开库仅保存汇总，不上传账号配置、原始会话日志、机器路径或事务备份。

局限：未构造真实无结构化输入工具、完全无脚本执行能力的客户端，也未验证网页/移动端/云端；空目录测试不是干净虚拟机。Windows 自动运行时准备仅限 x64。灵活模式的实际表现仍受宿主模型和上下文影响。
