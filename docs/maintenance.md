# 升级、运行时与故障恢复

首次使用从[安装教程](install.md)开始。本页集中说明后续升级、离线运行时、回滚、常见问题、卸载和手动兼容路径。所有命令的位置与占位符要求见对应章节。

## 升级与自定义内容

### 网页个人导入

网页导入与本地来源独立：重新运行 Windows 安装器不会更新网页个人条目。下载需要的 `plugin.zip` 和对应校验清单，在网页“个人 → 我创建的”打开已有 Auto Prompt 条目，检查详情或 `…` 菜单实际提供的编辑／更新入口。

同名 ZIP 的覆盖更新、重复导入或网页回滚尚未验证；不要把再次“上传插件”视为已经确认的原条目升级，也不要为升级先删除原插件。若界面没有明确更新入口，先记录当前条目和要求的操作，再确认处理方式。相同版本号也可能对应不同分发内容。

### 桌面本地更新

**升级到 v1.1.1：** 从[v1.1.1 发布页](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.1.1)重新下载整合包及校验清单，校验后运行安装器，再刷新客户端插件。升级前关闭相关编辑器；安装器保留独立自定义文件，已修改的程序文件仍会报告冲突。已登记的旧 Python 不符合[补丁策略](security-maintenance.md#运行时维护)时，安装器自动准备专属 Python 3.13.16；离线升级必须提供新版校验 ZIP 或兼容解释器，不能使用旧运行时 ZIP。详见[v1.1.1 发布说明](releases/v1.1.1.md)。

**历史 v1.0.2 有同版本修订。** 已安装 1.0.2 的用户也需重新下载整合包和 `SHA256SUMS.txt`，核对校验值，运行 `Install-Windows.cmd` 并刷新客户端；程序文件归属按内容摘要判断，不只比较版本号。

若客户端仍使用旧缓存，应通过客户端支持的本插件刷新/重装入口重新加载，不删除整个插件缓存。[发布说明](releases/v1.0.2.md)记录修订来源；重写前旧提交需按[历史映射](history/git-history.md)定位当前对象，不保证旧 SHA 可在新克隆检出。

关闭正在使用旧技能的聊天后，解压新包，运行同一入口。程序更新和用户配置分开处理：

- 旧版 v1.0.0 用已审计的分发文件摘要识别；新安装用 `.auto-prompt-install.json` 记录程序文件归属。
- 未修改的程序文件替换为新版；独立用户文件复制到新来源目录，内容不变。
- 修改过或删掉的程序文件、新版路径与用户文件冲突、重复/不同来源条目、未知配置形状均停止并说明问题。
- marketplace 的原名称、其他条目和本项目非 source 自定义字段保留，不拼接 JSON 文本。
- 将自定义规则存入单独的 user/ 或其他独立文件便于保存。保存并不代表自动应用；使用时明确引用。不要把机器配置或个人偏好提交到公开仓库。

遇到程序文件冲突：先单独保留你的修改并对比原版；由你决定迁入独立文件还是修改程序。将程序文件恢复为已识别的原分发版本后重试。不要删除归属清单来强制覆盖。安装器没有忽略冲突的 force 模式。

## 离线与显式运行时

本节及后续事务回滚、项目专属路径和隔离安装仅适用于桌面本地路径。

以下命令在解压文件夹的 PowerShell 中运行。把示例路径替换为实际路径；若执行策略阻止直接运行脚本，使用[首次安装的终端入口](install.md#3-运行安装器)，即 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File` 方式，并在末尾加对应参数。

~~~powershell
# 指定已有解释器；不兼容时自动准备专属版本，而不替换这个解释器
.\Install-Windows.ps1 -PythonPath 'C:\path\to\python.exe'

# 不复用共享解释器，准备专属运行时
.\Install-Windows.ps1 -DedicatedRuntime

# 在联网电脑取得官方文件后，复制到新电脑离线使用
.\Install-Windows.ps1 -DedicatedRuntime -Offline -RuntimeArchive 'C:\downloads\python-3.13.16-embed-amd64.zip'
~~~

固定 URL 和完整 SHA-256 记录在 [scripts/runtime-lock.json](../scripts/runtime-lock.json)；预先提供的 ZIP 仍必须校验。可从 Python 官方版本页下载相同文件，不修改 lock 来绕过校验。已兼容的运行时优先复用，`-RuntimeArchive` 仅在需要准备运行时时读取。

官方 ZIP 来自 [Python 3.13.16 发布页](https://www.python.org/downloads/release/python-31316/)的 **Windows embeddable package (64-bit)**，不是普通安装器；文件名为 `python-3.13.16-embed-amd64.zip`。当前下载版本、来源、许可与校验要求见[运行时维护](security-maintenance.md#运行时维护)；[v1.0.1 方案比较](history/v1.0.1-design.md#运行时方案比较)仅保留当时的设计取舍。

## 失败与回滚

### 安装失败

可捕获的失败仅恢复本次尝试写入的资源；未写入的共享登记保持现状。恢复前校验备份和当前内容；若本次写入后又被外部修改，保留该修改并报告 `recovery_conflict` 与事务 ID，其他仍可安全恢复的资源先恢复。关闭其他插件管理器后再处理冲突；摘要检查不是全系统排他锁。下载的新专属 Python 可保留为未引用文件，旧运行时与共享依赖不被删除。事务目录保留证据与旧文件，便于人工恢复。

### 恢复过程的保护措施

2026-10-07 恢复修订：共享登记和运行时指针以原子替换恢复，避免复制中断留下半份 JSON。

v1.1.0 安全修订在旧目录移入 `displaced` 后再次检查内容；并发编辑或无法读取时恢复最新目录（活动位置仍空缺时），停止安装并报告事务 ID。若活动位置已有其他内容则保留双方证据，不强行覆盖。检查相关目录、关闭编辑器后重试，不对冲突事务强制回滚；详见[保护范围](security-maintenance.md#输入与文件保护)。

目录恢复先在事务专属 `restore-stage` 中复制并校验旧文件；复制失败时当前程序目录仍保留。`restore.json` 记录准备阶段和摘要，切换时将当前目录保留在 `restore-displaced`。

恢复再次中断时，使用修订安装器和同一事务 ID 重试；仅在备份、准备目录、移开目录及登记证据一致时继续，不覆盖之后的用户改动。

**旧事务兼容边界：** schema 1 可读取，但 Windows 恢复已有文件缺少原 ACL 证据时拒绝自动回滚。无证据的缺失或部分复制状态需人工核对；不能凭目录缺失强行恢复，也不能用旧安装器绕过权限保护。

**v1.1.1 ACL 修订：** 新事务采用 schema 2，记录内容与权限快照，备份和原子写入临时文件在写入前就限制访问。升级及回滚保留 Windows 文件、目录和配置的 owner、primary group、DACL；仅权限被后来修改时也停止回滚。Windows 旧 schema 1 事务如需恢复已有文件，会因缺少原 ACL 证据而拒绝自动恢复；不要用旧安装器强行绕过。保留活动文件、事务备份和独立权限备份，人工核对后恢复。新版可以安全升级旧程序，但不能补回此前已经丢失的权限。范围和限制见[安装权限保护](security-maintenance.md#安装权限保护v111)。本修订随 v1.1.1 整合包的安装器提供。

运行时准备由独立的 `runtime.prepare.lock` 文件句柄串行化，获取锁后重新检查可用解释器；最多等候 30 秒，仍忙时明确提示稍后重试。正常结束或进程被终止时由系统释放句柄并删除锁，不需要手工删除正在使用的运行时锁。这与下述 Python 安装事务的 `install.lock` 是两个不同的锁，不修改系统依赖或全局配置。

### 使用事务 ID 回滚

在当前整合包的解压文件夹中，使用安装器打印的 transaction ID：

~~~powershell
.\Install-Windows.ps1 -Rollback 0123456789abcdef0123456789abcdef
~~~

示例 ID 必须替换为你本次安装的实际 ID；隔离安装回滚时同时传原 `-HomeDirectory`。

安装后若你修改了来源目录或其他插件更新了同一 marketplace，显式 `-Rollback` 会报告冲突并停止，不覆盖后来的内容。先比较事务 `before/` 与当前文件，合并本项目的必要恢复项。不要整份覆盖客户端配置。

### 安装进程被强制结束

进程被强制结束后：关闭仍在运行的安装器，检查项目 `install.lock` 中记录的 PID 确已结束；仅删除 `.codex/auto-prompt/install.lock` 这个锁文件，再使用对应事务 ID 回滚。

事务 ID 可从 `.codex/auto-prompt/transactions/` 下的 `transaction.json` 找到。当前内容等于旧态或计划新态时可恢复。

另支持 `applying/recovery_conflict` 状态下旧目录已移入 `displaced`、新 `stage` 尚未落位的中断：仅当 `displaced`、`stage` 和 `before/` 备份的摘要全部符合事务记录时，允许恢复缺失目标目录。

修订安装器还支持有 `restore.json` 与完整 `restore-stage`／`restore-displaced` 证据的恢复切换中断，包括已提交安装的回滚。仅目录缺失或中间证据遭修改都不能作为自动恢复依据。新安装器可读取 v1.0.1 的 schema 1 事务，但 Windows 恢复已有文件仍受原 ACL 证据限制；旧安装器不认识新增恢复证据，不要用旧安装器继续新修订的中断回滚。人工改动过的中间态需对比处理。

真实断电及文件系统损坏未验收，不能将进程中断测试当作断电恢复保证。

回滚后在 ChatGPT 刷新/重新安装本项目插件并新建聊天，确认加载旧版本。宿主管理的缓存不是安装器的事务对象。

## 常见问题

### 网页路径

- 找不到“上传插件”：入口受账号、工作区和功能权限影响，不能凭公共插件页推断具备导入权限。
- 选了错误文件：网页入口使用 `auto-prompt-skill-1.1.1-plugin.zip`，保持 ZIP。单技能包缺少插件清单，桌面整合包包含额外安装材料；按推荐文件重新选择。
- 导入后找不到：确认登录同一账号／工作区，切换到“个人 → 我创建的”，打开条目检查安装状态，再新建聊天用 `@` 搜索。
- 上传出现格式或规则错误：保留错误全文或截图，先核对校验值与文件名；包结构和账号检查通过后再处理具体问题，不凭“上传入口可见”宣称导入一定成功。
- 能生成提示词但严格模式无法运行：按[严格模式环境检查](install.md#6-严格模式先检查执行环境)区分工具缺失、原文件不可访问和运行时不符合策略。网页 ZIP 不准备解释器，Windows 安装器也不会自动修复云端 Python；受阻时选择灵活模式或已验收的桌面本地路径，不冒称严格成功。
- 导入后要求开发者认证、提交审核或公开发布：先确认是否进入了公开发布流程，而非个人导入流程。

### 桌面本地路径

- 归属清单或事务日志损坏：安装器明确报告清单/日志及结构问题，停止且保留原文件。先保留证据，对比可信备份并恢复完整清单或日志后再试；不要删除归属清单、拼接日志或强制覆盖来绕过检查。
- 下载失败/TLS 或代理错误：修复联网环境后重新运行，或用官方 ZIP 和 `-RuntimeArchive`；不要关闭证书校验。
- SHA-256 不匹配：安装失败，原 ZIP 保留供检查。另取官方同版本 ZIP；不要编辑校验值接受损坏文件。
- 依赖缺失或已有 Python 不兼容：安装器准备专属版本；如果宿主后来删除了复用的 Python，重新运行入口即可修复指针。
- Windows ARM64/32 位：自动准备未验收，会明确停止。可使用兼容 Python 的手动安装路径，但本次不保证该平台宿主表现。
- 客户端仍显示旧版本：来源已更新不代表宿主缓存已刷新，按客户端实际支持的刷新/重装本插件方式处理。
- 没有结构化提问工具：技能改用文字选项，无需额外插件。
- 严格模式无法执行：明确报告未运行；修复运行时或选择灵活模式，不以模型结果冒称严格输出。
- 目录是符号链接/junction：安装器拒绝自动写入，选择普通目录；不更改系统设置来绕过。
- 隔离目录路径过长：Windows PowerShell 5.1 解压可能受 260 字符限制，选择较短的 `-HomeDirectory`；安装器会说明路径问题，不修改全局长路径设置。
- 移动整个用户目录后严格启动器报路径不存在：`runtime.json` 仍记录绝对路径。到新位置重新运行安装器（隔离目录需传新 `-HomeDirectory`），有兼容解释器或官方 ZIP 时可离线修复。不要直接修改全局 PATH。

## 卸载

### 网页个人导入

在网页版“个人 → 我创建的”打开 Auto Prompt 条目，按实际详情／`…` 菜单提供的卸载或删除功能处理。卸载与删除个人条目可能是不同操作，具体菜单或回滚行为尚未验证；删除前保留自己的修改和原 ZIP。网页操作不清理 Windows 的本地程序、运行时或事务目录。

### 桌面本地路径

1. 在 ChatGPT 的 Plugins 中仅卸载/禁用 Auto Prompt Skill。
2. 如需移除本地来源，先备份后，仅从个人 `marketplace.json` 的 plugins 数组移除 name 为 auto-prompt-skill 且 source 指向本项目的条目，保留所有其他内容。
3. 仅删除/移走 `.codex/plugins/local-auto-prompt-skill`；先保留其中的独立自定义文件。
4. 确认不再使用本项目后，可删除/移走 `.codex/auto-prompt` 专属运行时、缓存和事务备份。不要删除共享 Python 或 `.codex`、`.agents` 整个目录。
5. 不操作旧 Auto Prompt 部署、CYX-MEMORY 或其他插件。

## 项目专属路径

默认用户目录为 Windows 的 `%USERPROFILE%`；指定 `-HomeDirectory` 时以下路径相对于所选目录：

- 程序来源：`.codex/plugins/local-auto-prompt-skill/`
- 目录登记：`.agents/plugins/marketplace.json`，仅本项目条目
- 运行时指针：`.codex/auto-prompt/runtime.json`
- 可选下载运行时：`.codex/auto-prompt/runtimes/python-3.13.16-x64/`
- 官方 ZIP 缓存：`.codex/auto-prompt/downloads/`
- 事务备份：`.codex/auto-prompt/transactions/<ID>/`

安装器不编辑整个客户端 `config.toml`，也不自动复制其他插件。运行时不加 PATH，不安装 pip，不通过 py/pymanager 引发共享 Python 安装。

已存在的专属固定版本优先；没有显式指定 Python 时，先读取 UTF-8 `runtime.json` 并验证已登记解释器，再查宿主固定路径及 PATH；登记损坏、文件不存在或不兼容时继续发现，找不到才准备专属运行时。嵌入式包保留原 `LICENSE.txt` 和依赖文件。

`Install-Windows.ps1` 默认仍输出机器可读 JSON，新增 `selfTest.status=passed` 表示启动器自检通过；传 `-Interactive` 可显示中文摘要，CMD 自动选择此模式。直接 Python 安装入口保持兼容，仅显式 `--check-launcher` 才执行 Windows 自检。回滚恢复旧文件，可能恢复旧版限制，不把回滚报告成新版自检通过。

CMD 仅在自身子进程中重建 Windows PowerShell 模块搜索环境，避免继承 PowerShell 7 的 PSModulePath 导致 Get-FileHash 等命令不可用，不更改用户或系统环境变量。

## 隔离验收，不影响实际用户配置

可选：用于测试安装，不会让真实用户的客户端自动加载隔离目录。把示例目录换成专门的测试目录，在解压文件夹运行：

~~~powershell
.\Install-Windows.ps1 -HomeDirectory 'C:\temporary\auto-prompt-test-user' -DedicatedRuntime
~~~

该参数把程序、运行时、目录条目和备份全部指向隔离用户根目录。`-DedicatedRuntime` 忽略主机上的共享解释器，用于验收“目标环境为空”路径；不会创建 Windows 用户账号或模拟 ChatGPT 登录。

## 手动兼容路径

已有符合[维护策略](security-maintenance.md#运行时维护)的 Python 时，在仓库根目录或整合包解压文件夹运行。以下为两种替代方式，选一种；不会自动下载解释器。

登记插件来源：

~~~sh
python scripts/install.py --mode plugin
~~~

仅安装技能文件：

~~~sh
python scripts/install.py --mode skill
~~~

skill 模式安装到 `.agents/skills/auto-prompt`，保留旧版行为；不要与插件方式重复启用。其他宿主的专门适配不在本教程的验收范围内；macOS/Linux 需要自行提供兼容解释器。

来源：[官方本地插件目录](https://developers.openai.com/plugins/build/plugins)、[技能发现与调用](https://learn.chatgpt.com/docs/build-skills)。

严格脚本也可以直接运行，不必先登记客户端插件。在同一根目录终端执行：

~~~sh
python skills/auto-prompt/scripts/render_prompt.py --input examples/chatgpt.json
~~~

正常结果是固定模板生成的提示词正文；这仅验证脚本，不验证 ChatGPT 已加载技能。Windows 已安装用户也可在安装的技能目录调用 `scripts/Run-Strict.ps1 -InputPath <JSON文件> -OutputPath <输出文件>`，把占位符替换为实际路径；启动器读取本用户的运行时登记，不联网安装依赖。
