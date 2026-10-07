# 安装、升级、恢复与卸载 · v1.0.2

本轮目标宿主为连接本机执行环境的 ChatGPT 桌面客户端。自动依赖准备仅为 Windows x64；文件格式与旧 Codex 安装模式保留，不把兼容格式等同于完成其他宿主验收。

## 责任边界

| 步骤 | 安装器 | 用户／宿主 |
| --- | --- | --- |
| 安装 ChatGPT、登录账号、选择本地环境 | 不代办 | 用户完成 |
| 检查 Python 能力 | 自动隔离探测，检查 3.9–3.14 和所需标准库 | 可显式指定已有 Python |
| 缺少／不兼容运行时 | 下载固定官方 Python 到专属目录，SHA-256 校验后使用 | 网络受限时提供官方 ZIP |
| 文件、个人 marketplace、运行时路径登记 | 自动安装与事务备份 | 冲突时由用户明确解决 |
| 插件安装／刷新、权限、启用、新聊天 | 打印下一步 | 在实际客户端入口完成 |
| ChatGPT 对话表现 | 自动测试不能证明 | 按验收清单实测 |

## 新电脑安装

1. 安装、登录 ChatGPT 桌面客户端，确认有本地执行与个人本地 Plugins 来源入口。没有该能力的环境不属于本次自动安装验收范围。
2. 从 [v1.0.2 Release](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.0.2) 下载整合包，核对其 SHA-256 与随包外提供的 SHA256SUMS.txt；解压。
3. 双击 Install-Windows.cmd；无需提前装 Python。也可运行：
~~~powershell
.\Install-Windows.ps1
~~~
4. CMD 显示中文摘要：安装位置、Python、自检结果、事务 ID（有变更时）和客户端待启用步骤。安装器实际调用已安装的严格启动器，核对固定样例摘要；自检失败不报告成功，有本次写入时按事务规则恢复。没有报成功时按错误处理，不跳过。
5. 重启 ChatGPT 桌面客户端，在 Plugins 选择对应个人本地来源，安装或刷新 Auto Prompt Skill。已有旧版本时确认实际缓存/已加载技能版本变为 1.0.2；只有来源目录变化不算客户端完成升级。
6. 新建连接本机的聊天，选择 Auto Prompt，执行 [验收清单](chatgpt-acceptance.md)。

本地来源按官方 personal marketplace 格式登记。账号政策和客户端版本可能影响入口；不保证所有网页、移动端或云端都有该入口。把 ZIP 上传为聊天附件不会自动安装本地技能。

## 项目专属路径

相对于所选用户目录：
- 程序来源：.codex/plugins/local-auto-prompt-skill/
- 目录登记：.agents/plugins/marketplace.json，仅本项目条目
- 运行时指针：.codex/auto-prompt/runtime.json
- 可选下载运行时：.codex/auto-prompt/runtimes/python-3.13.12-x64/
- 官方 ZIP 缓存：.codex/auto-prompt/downloads/
- 事务备份：.codex/auto-prompt/transactions/<ID>/

安装器不编辑整个客户端 config.toml，也不自动复制其他插件。运行时不加 PATH，不安装 pip，不通过 py/pymanager 引发共享 Python 安装。已存在的专属固定版本优先；没有显式指定 Python 时，先读取 UTF-8 runtime.json 并验证已登记解释器，再查宿主固定路径及 PATH；登记损坏、文件不存在或不兼容时继续发现，找不到才准备专属运行时。嵌入式包保留原 LICENSE.txt 和依赖文件。

Install-Windows.ps1 默认仍输出机器可读 JSON，新增 selfTest.status=passed 表示启动器自检通过；传 -Interactive 可显示中文摘要，CMD 自动选择此模式。直接 Python 安装入口保持兼容，仅显式 --check-launcher 才执行 Windows 自检。回滚恢复旧文件，可能恢复旧版限制，不把回滚报告成新版自检通过。

CMD 仅在自身子进程中重建 Windows PowerShell 模块搜索环境，避免继承 PowerShell 7 的 PSModulePath 导致 Get-FileHash 等命令不可用，不更改用户或系统环境变量。

## 离线与显式运行时

~~~powershell
# 指定已有解释器；不兼容时自动准备专属版本，而不替换这个解释器
.\Install-Windows.ps1 -PythonPath 'C:\path\to\python.exe'

# 不复用共享解释器，准备专属运行时
.\Install-Windows.ps1 -DedicatedRuntime

# 在联网电脑取得官方文件后，复制到新电脑离线使用
.\Install-Windows.ps1 -DedicatedRuntime -Offline -RuntimeArchive 'C:\downloads\python-3.13.12-embed-amd64.zip'
~~~

固定 URL 和完整 SHA-256 记录在 scripts/runtime-lock.json；预先提供的 ZIP 仍必须校验。可从 Python 官方版本页下载相同文件，不修改 lock 来绕过校验。已兼容的运行时优先复用，-RuntimeArchive 仅在需要准备运行时时读取。

## 隔离验收，不影响实际用户配置

~~~powershell
.\Install-Windows.ps1 -HomeDirectory 'C:\temporary\auto-prompt-test-user' -DedicatedRuntime
~~~

该参数把程序、运行时、目录条目和备份全部指向隔离用户根目录。-DedicatedRuntime 忽略主机上的共享解释器，用于验收“目标环境为空”路径；不会创建 Windows 用户账号或模拟 ChatGPT 登录。

## 升级与自定义内容

本次按用户要求保持 1.0.2 版本号。旧 1.0.2 也需重新下载附件，核对新的 SHA256SUMS.txt，运行安装器并刷新客户端；程序文件归属按内容摘要判断，不只比较版本号。若客户端仍使用旧缓存，应通过客户端支持的本插件刷新/重装入口重新加载，不删除整个插件缓存。发布说明记录修订来源；旧提交仍可用其完整提交号检出。

关闭正在使用旧技能的聊天后，解压新包，运行同一入口。程序更新和用户配置分开处理：
- 旧版 v1.0.0 用已审计的分发文件摘要识别；新安装用 .auto-prompt-install.json 记录程序文件归属。
- 未修改的程序文件替换为新版；独立用户文件复制到新来源目录，内容不变。
- 修改过或删掉的程序文件、新版路径与用户文件冲突、重复/不同来源条目、未知配置形状均停止并说明问题。
- marketplace 的原名称、其他条目和本项目非 source 自定义字段保留，不拼接 JSON 文本。
- 将自定义规则存入单独的 user/ 或其他独立文件便于保存。保存并不代表自动应用；使用时明确引用。不要把机器配置或个人偏好提交到公开仓库。

遇到程序文件冲突：先单独保留你的修改并对比原版；由你决定迁入独立文件还是修改程序。将程序文件恢复为已识别的原分发版本后重试。不要删除归属清单来强制覆盖。安装器没有忽略冲突的 force 模式。

## 失败与回滚

可捕获的失败仅恢复本次尝试写入的资源；未写入的共享登记保持现状。恢复前校验备份和当前内容；若本次写入后又被外部修改，保留该修改并报告 recovery_conflict 与事务 ID，其他仍可安全恢复的资源先恢复。关闭其他插件管理器后再处理冲突；摘要检查不是全系统排他锁。下载的新专属 Python 可保留为未引用文件，旧运行时与共享依赖不被删除。事务目录保留证据与旧文件，便于人工恢复。

2026-10-07 恢复修订：共享登记和运行时指针以原子替换恢复，避免复制中断留下半份 JSON。目录恢复先在事务专属 restore-stage 中复制并校验旧文件；复制失败时当前程序目录仍保留。restore.json 记录准备阶段和摘要，切换时将当前目录保留在 restore-displaced。恢复再次中断时，使用修订安装器和同一事务 ID 重试；仅在备份、准备目录、移开目录及登记证据一致时继续，不覆盖之后的用户改动。旧 schema 1 事务仍可读取；旧安装器已经留下的无证据缺失或部分复制状态仍需人工对比，不能凭目录缺失强行恢复。

运行时准备由独立的 runtime.prepare.lock 文件句柄串行化，获取锁后重新检查可用解释器；最多等候 30 秒，仍忙时明确提示稍后重试。正常结束或进程被终止时由系统释放句柄并删除锁，不需要手工删除正在使用的运行时锁。这与下述 Python 安装事务的 install.lock 是两个不同的锁，不修改系统依赖或全局配置。

使用打印出的 transaction ID：
~~~powershell
.\Install-Windows.ps1 -Rollback 0123456789abcdef0123456789abcdef
~~~
示例 ID 必须替换为你本次安装的实际 ID；隔离安装回滚时同时传原 -HomeDirectory。

安装后若你修改了来源目录或其他插件更新了同一 marketplace，显式 -Rollback 会报告冲突并停止，不覆盖后来的内容。先比较事务 before/ 与当前文件，合并本项目的必要恢复项。不要整份覆盖客户端配置。

进程被强制结束后：关闭仍在运行的安装器，检查项目 install.lock 中记录的 PID 确已结束；仅删除 .codex/auto-prompt/install.lock 这个锁文件，再使用对应事务 ID 回滚。事务 ID 可从 .codex/auto-prompt/transactions/ 下的 transaction.json 找到。当前内容等于旧态或计划新态时可恢复。另支持 applying/recovery_conflict 状态下旧目录已移入 displaced、新 stage 尚未落位的中断：仅当 displaced、stage 和 before/ 备份的摘要全部符合事务记录时，允许恢复缺失目标目录。修订安装器还支持有 restore.json 与完整 restore-stage/restore-displaced 证据的恢复切换中断，包括已提交安装的回滚。仅目录缺失或中间证据遭修改都不能作为自动恢复依据。新安装器仍可读取 v1.0.1 的 schema 1 事务；旧安装器不认识新增恢复证据，不要用旧安装器继续新修订的中断回滚。人工改动过的中间态需对比处理。真实断电及文件系统损坏未验收，不能将进程中断测试当作断电恢复保证。

回滚后在 ChatGPT 刷新/重新安装本项目插件并新建聊天，确认加载旧版本。宿主管理的缓存不是安装器的事务对象。

## 常见问题

- 归属清单或事务日志损坏：安装器明确报告清单/日志及结构问题，停止且保留原文件。先保留证据，对比可信备份并恢复完整清单或日志后再试；不要删除归属清单、拼接日志或强制覆盖来绕过检查。

- 下载失败/TLS 或代理错误：修复联网环境后重新运行，或用官方 ZIP 和 -RuntimeArchive；不要关闭证书校验。
- SHA-256 不匹配：安装失败，原 ZIP 保留供检查。另取官方同版本 ZIP；不要编辑校验值接受损坏文件。
- 依赖缺失或已有 Python 不兼容：安装器准备专属版本；如果宿主后来删除了复用的 Python，重新运行入口即可修复指针。
- Windows ARM64/32 位：自动准备未验收，会明确停止。可使用兼容 Python 的手动安装路径，但本次不保证该平台宿主表现。
- 客户端仍显示旧版本：来源已更新不代表宿主缓存已刷新，按客户端实际支持的刷新/重装本插件方式处理。
- 没有结构化提问工具：技能改用文字选项，无需额外插件。
- 严格模式无法执行：明确报告未运行；修复运行时或选择灵活模式，不以模型结果冒称严格输出。
- 目录是符号链接/junction：安装器拒绝自动写入，选择普通目录；不更改系统设置来绕过。
- 隔离目录路径过长：Windows PowerShell 5.1 解压可能受 260 字符限制，选择较短的 -HomeDirectory；安装器会说明路径问题，不修改全局长路径设置。

- 移动整个用户目录后严格启动器报路径不存在：runtime.json 仍记录绝对路径。到新位置重新运行安装器（隔离目录需传新 -HomeDirectory），有兼容解释器或官方 ZIP 时可离线修复。不要直接修改全局 PATH。

## 卸载

1. 在 ChatGPT 的 Plugins 中仅卸载/禁用 Auto Prompt Skill。
2. 如需移除本地来源，先备份后，仅从个人 marketplace.json 的 plugins 数组移除 name 为 auto-prompt-skill 且 source 指向本项目的条目，保留所有其他内容。
3. 仅删除/移走 .codex/plugins/local-auto-prompt-skill；先保留其中的独立自定义文件。
4. 确认不再使用本项目后，可删除/移走 .codex/auto-prompt 专属运行时、缓存和事务备份。不要删除共享 Python 或 .codex、.agents 整个目录。
5. 不操作旧 Auto Prompt 部署、CYX-MEMORY 或其他插件。

## 保留的手动兼容路径

已有 Python 3.9–3.14 时：
~~~sh
python scripts/install.py --mode plugin
python scripts/install.py --mode skill
~~~
skill 模式安装到 .agents/skills/auto-prompt，保留旧版行为；不要与插件方式重复启用。本轮没有新增其他宿主的专门适配，也没有自动为 macOS/Linux 准备解释器。

来源：[官方本地插件目录](https://developers.openai.com/plugins/build/plugins)、[技能发现与调用](https://learn.chatgpt.com/docs/build-skills)。
