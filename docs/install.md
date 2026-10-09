# 安装与使用 · v1.1.0

> v1.1.0 安全性修复版：加强文件、安装事务、输入和运行时保护。变更与升级限制见[发布说明](release-v1.1.0.md)。

最新步骤以[GitHub 安装教程](https://github.com/Saki-174/auto-prompt-skill/blob/main/docs/install.md)为准；现有 Release 整合包内的文档可能早于本次更新。

本教程分成两条独立路径：**Windows 电脑浏览器中的 ChatGPT 网页版**，以及 **Windows x64 的 ChatGPT 桌面客户端本地 Work**。先选环境，再下载对应文件；它们不共用安装步骤。

[返回首页](../README.md) · [网页版安装](#一windows-电脑浏览器网页版安装) · [桌面本地安装](#二windows-桌面客户端本地安装) · [升级](#升级与自定义内容) · [回滚](#失败与回滚) · [常见问题](#常见问题) · [卸载](#卸载)

## 先选环境与文件

| 你要在哪里使用 | 应下载的文件 | 接下来做什么 |
| --- | --- | --- |
| 浏览器中的 ChatGPT 网页版 | `auto-prompt-skill-1.1.0-plugin.zip` | 保持压缩状态，在网页插件页“上传插件” |
| ChatGPT Windows x64 桌面客户端的本地 Work | `auto-prompt-skill-1.1.0-bundle.zip` | 解压，运行 Windows 安装器，再在客户端启用 |

另有 `auto-prompt-1.1.0-skill.zip`，用于已有单技能导入／发现方式的宿主；本教程的网页“上传插件”和桌面安装器路径均使用上表文件。GitHub 的 **Source code** 压缩包也不是这两条路径的推荐下载项。

所有文件均在 [v1.1.0 发布页](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.1.0)的 **Assets** 中，校验清单是 [SHA256SUMS.txt](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.0/SHA256SUMS.txt)。两条路径都需要可登录的 ChatGPT 账号和相应插件入口，账号或工作区政策可能限制可见功能。

## 一、Windows 电脑浏览器：网页版安装

适合主要在浏览器使用 ChatGPT、希望进行日常灵活改写的场景。以下步骤说明网页上传入口，不构成“无需本机安装器或 Python”的验证；网页依赖条件和脚本执行能力尚需在隔离环境中确认。

### 1. 下载网页插件包

1. 在 Windows 浏览器打开 [v1.1.0 发布页](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.1.0)。
2. 展开 **Assets**，下载 [auto-prompt-skill-1.1.0-plugin.zip](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.0/auto-prompt-skill-1.1.0-plugin.zip) 和 `SHA256SUMS.txt` 到同一下载文件夹。
3. 在该文件夹打开 PowerShell，用以下只读命令核对文件：

~~~powershell
Get-FileHash -LiteralPath '.\auto-prompt-skill-1.1.0-plugin.zip' -Algorithm SHA256
Get-Content -LiteralPath '.\SHA256SUMS.txt'
~~~

将第一条输出的 `Hash` 与清单中 **plugin.zip 同名文件**那一行比较；字母大小写可忽略。相同才继续，不同则重新下载。**保持 ZIP 压缩状态，不解压，也不改扩展名。**

### 2. 打开网页的上传入口

1. 在浏览器登录 [ChatGPT](https://chatgpt.com/)。
2. 点击左侧导航的 **“插件”**。页面标题也应为“插件”，右上方有“搜索插件”输入框。
3. 点击**搜索框右侧的圆形 `＋` 按钮**。
4. 在展开菜单中选择 **“上传插件”**。

导入现有包请选择“上传插件”，而不是“创建插件”或“创建自定义 MCP 服务器”。本项目不需要创建 MCP 服务。将 ZIP 附在普通聊天里不等于通过这个入口安装。

如果没有“插件”或“上传插件”，先核对当前账号、工作区和功能权限，或使用下面的桌面本地路径。不要假定所有账号都有相同菜单。若出现开发者身份、公开提交或审核页面，应先确认是否进入了发布流程；本教程的目标是个人导入和使用，不是公开发布。

### 3. 选择 ZIP，确认导入结果

1. 在文件选择框中选中刚下载的 `auto-prompt-skill-1.1.0-plugin.zip`。
2. 等待校验。检查“新插件”窗口是否显示所选文件名，以及绿色 **“导入成功”** 提示；出现错误时先处理错误，不继续安装。
3. 点击右下角 **“查看插件”**。
4. 在插件页切换到 **“个人”**，在 **“我创建的”** 中找到 **Auto Prompt Skill**，打开详情。
5. 如果详情仍提供“安装”或安装用 `＋` 按钮，完成安装；如果已经显示已安装，直接进入下一步。

“导入成功”确认包已被接收；“我创建的”确认个人条目存在；新聊天中实际调用才检查可用性。不要仅凭图标或导入提示认定严格模式也可运行。

核对加载身份与版本时，先记录所选条目及详情页实际提供的信息。有文件读取工具才能进一步核对插件清单；只凭模型自述不能确认版本，没有工具时保留为未验证。完整步骤见[来源、版本与宿主能力验收](chatgpt-acceptance.md#第一阶段确认来源版本与宿主能力)。

### 4. 新建聊天，调用技能

1. 点击 **“新聊天”**。
2. 在输入框键入 `@`，搜索 **Auto Prompt**，选择实际显示的 Auto Prompt 插件或其技能。
3. 发送：

~~~text
请调用 Auto Prompt 技能。
~~~

应开始简短引导，例如询问目标 Agent 或原始需求。随后发送：

~~~text
目标 Agent：ChatGPT
需求：帮我学习概率，先用生活例子解释，再给两道练习题。
约束：中文，不使用微积分。
~~~

预期生成可复制的教学提示词，保留例子、题数、语言和数学范围；不会直接开始讲概率。生成正文以外的建议不应冒充你已确认的要求。仅自然语言输出符合预期，不足以证明实际读取了哪个技能文件；可同时检查对话中的插件选择和使用标识。

如果 `@` 找不到插件，回到“个人 → 我创建的”检查安装状态，确认仍是同一账号／工作区，再新建聊天。若仍不可用，保留实际界面或错误以便排查，不把上传成功当作调用成功。

若插件标签显示“点击以重试”，先记录加载失败，不把随后普通聊天的输出计为技能验收。若实际入口弹出 ChatGPT Work 引导并显示“使用 Plus 解锁”，当前账号在该入口的使用权限尚不满足；可使用已有相应权限的账号／客户端，或保留此项未验证。不要为解决账号权限重复安装本地 Python，也不需要为验收购买套餐。仅这个入口的观察不能代表其他账号或聊天模式。

### 5. 检查修改与撤销

在同一聊天中继续发送：

~~~text
把练习题改为三道，并在每题后直接附答案和解析。其他要求保持不变。
~~~

预期更新为三道题并附答案解析，同时保留中文、不用微积分和生活例子。再发送：

~~~text
撤销刚才修改。
~~~

预期恢复上一份完整提示词。若上一份包含“先不给答案”，该要求也应恢复；它是否适合你，应以你的确认需求为准。

以上是验收步骤，不代表各账号或浏览器均已通过。网页端的依赖条件、完整引导、跨任务隔离、结构化提示框及严格脚本执行尚未完成独立验证，见[验证边界](validation.md#网页版验证边界)。

### 6. 严格模式：先检查执行环境

**网页导入步骤不会调用 Windows 安装器，也不会准备 Python。** 网页插件包包含技能、渲染脚本和模板，不包含解释器。项目现有的自动运行时准备入口仅支持 Windows x64 本地环境；尚无已验收的网页云端自动准备路径。导入完成后，灵活改写与严格执行需分别检查。

在新建的 Work 对话中选择 Auto Prompt，按以下顺序验收；可以让当前宿主执行检查，但必须查看实际工具记录，不能只接受文字自述：

1. **确认实际执行位置**：记录本轮使用云端环境还是已获准连接的本机。浏览器运行在 Windows 上，不代表脚本在 Windows 上执行；本机 runtime.json 不会因上传插件自动成为云端运行时登记。
2. **确认工具、原文件与来源关联**：当前会话需要执行工具，并能读取所选插件的 scripts/runtime_policy.py、scripts/render_prompt.py 和对应模板。所选云端 skill 资源与文件系统缓存分别记录，以实际包关联和内容比对确认执行文件归属，不凭同名或版本号认定。资源与缓存不同或来源无法确认时，先记录“所选技能执行文件来源未验证”，停止严格验收；没有工具或文件不可访问时记录“未执行”。
3. **检查解释器**：取得实际 Python 路径和版本，使用该路径执行插件原 scripts/runtime_policy.py。维护策略以当前插件原文件为准，版本门槛见[运行时维护](security-maintenance.md#运行时维护)。策略检查退出码为 0 才继续本次验收；退出 2 时保留原错误，不修改策略或改用另写的脚本。
4. **复用完整输入**：已有完整 JSON 时原样使用，不重复询问已给出的目标 Agent，也不擅自改 profile、strictMode 或约束。使用上一步同一解释器执行原 scripts/render_prompt.py --input <JSON文件> --format text --output <输出文件>；占位符由执行宿主替换为其实际可访问路径。
5. **核对两次结果**：同一 JSON、脚本和模板运行两次，保留实际命令、退出码、输出字节数、SHA-256 和输出文件，比较原始字节。验收 JSON 与预期摘要见[严格结果与兼容](chatgpt-acceptance.md#严格结果与兼容)。未启动渲染时，这些渲染指标为“不适用”。

**运行时不足时怎么继续？** 可明确选择网页灵活模式，或使用已准备兼容 Python 的[桌面本地 Work](#二windows-桌面客户端本地安装)完成严格转换。若云端已有符合策略的解释器，可核验其真实路径后重新检查；当前项目不提供经验证的云端下载安装步骤。不要反复上传 ZIP、升级本机共享 Python 或降低门槛来冒充云端修复。本地安装不能修复一个没有连接本机的云端解释器。

官方说明允许在满足工作区同步、连接和权限条件时，通过网页继续使用已连接电脑的资源，见[跨设备继续 Work](https://learn.chatgpt.com/docs/get-started-with-work#continue-work-across-devices)。这属于另一种执行路径，仍需核对本轮实际工具和运行时；本项目尚未验收该连接路径，不把它作为通用的一键解决办法。

目前 Work 回传报告中，被检查的同名缓存策略要求 3.12 ≥3.12.15，所报告 3.12.14、3.12.3 均低于该门槛；后续回传指出所选云端资源与此缓存内容不同，不能将该检查归属于所选条目。相同 JSON 在本机已核验文件与 Python 3.13.16 下独立复核。来源和运行时分别检查，见[Work 检查与验证边界](validation.md#work-手工操作回传检查2026-10-09)。本机成功、缓存检查及自然语言回复均不能替代所选网页插件的严格执行验证。


## 二、Windows 桌面客户端：本地安装

### 1. 确认使用环境

在 Windows x64 电脑上安装并登录 ChatGPT 桌面客户端，确认账号支持连接本机执行环境的 **Work** 和本地 **Plugins** 来源。宿主安装、登录、授权及最终启用由你完成；安装器不会代办这些步骤。

入口受账号、客户端及工作区设置影响。没有入口时，先确认宿主支持情况，不要把 ZIP 上传到聊天当作安装。官方依据：[本地插件目录](https://developers.openai.com/plugins/build/plugins)、[ChatGPT 本地 Work](https://learn.chatgpt.com/docs/use-chatgpt)。

无需提前安装 Python。安装器会复用符合[维护策略](security-maintenance.md#运行时维护)的 Python；找不到时，从 Python 官方下载固定的 3.13.16 Windows x64 嵌入式运行时，校验后放入项目专属目录。首次下载约 10.9 MB，需要联网；有兼容解释器或已校验的官方 ZIP 时可[离线安装](#离线与显式运行时)。

自动依赖准备仅限 Windows x64。其他平台保留[手动兼容路径](#手动兼容路径)，不等于已完成其他宿主或平台的客户端验收。本地安装不会自动同步到网页、移动端或云端；严格脚本能离线运行，ChatGPT 对话仍由宿主服务提供。

### 2. 下载并核对文件

打开 [v1.1.0 发布页](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.1.0)，展开 **Assets**，下载这两个文件到同一文件夹：

- [auto-prompt-skill-1.1.0-bundle.zip](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.0/auto-prompt-skill-1.1.0-bundle.zip)：含安装器、技能、脚本及文档。
- [SHA256SUMS.txt](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.0/SHA256SUMS.txt)：三个 ZIP 的校验清单。

**桌面本地安装使用整合包。** 上面的网页路径使用 `plugin.zip`；`skill.zip` 用于已有单技能导入方式。它们不含本地安装器；GitHub 的 **Source code** 压缩包也不是推荐下载项。

在下载文件夹打开 PowerShell，运行以下只读命令：

~~~powershell
Get-FileHash -LiteralPath '.\auto-prompt-skill-1.1.0-bundle.zip' -Algorithm SHA256
Get-Content -LiteralPath '.\SHA256SUMS.txt'
~~~

将 `Hash` 与清单中整合包同一行的值比较；字母大小写可忽略。相同才继续，不同则重新下载，不修改清单来绕过校验。

在文件资源管理器中对 ZIP 选择“全部解压”。进入解压后的 `auto-prompt-skill` 文件夹，确认能看到 `Install-Windows.cmd`、`Install-Windows.ps1`、`scripts` 和 `skills`。后续终端命令均在此文件夹运行，除非另行说明。

### 3. 运行安装器

双击 **`Install-Windows.cmd`**，等待检查或下载结束。正常结果包含：

- “安装完成”或“文件已是当前内容，无需重复安装”。
- “严格脚本自检：通过”。
- 安装位置、Python 路径、本地来源名称和客户端待启用步骤。
- 有变更时的**恢复事务 ID**，请保留以备回滚。

安装器实际运行已安装的严格启动器并核对固定输出；失败时不报告成功。遇到错误先阅读提示和[常见问题](#常见问题)，不要跳过自检。

需要终端方式时，在解压文件夹的 PowerShell 中运行以下替代命令，效果同 CMD 入口：

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Install-Windows.ps1 -Interactive
~~~

`-ExecutionPolicy Bypass` 仅作用于这次子进程，不修改系统执行策略。安装器只使用标准库，不需要 pip、npm、Ollama、Docker 或常驻服务；不升级共享 Python，不修改全局 PATH 或注册表。

### 4. 打开桌面插件页并选择本地来源

完成安装器后，在这台 Windows 电脑上操作桌面应用：

1. 打开 **ChatGPT 桌面客户端**，登录后进入本地 Work 环境。确认当前窗口是已安装的桌面应用；浏览器中的 `chatgpt.com` 应走上面的网页版路径。
2. 在桌面应用导航中打开 **“插件 / Plugins”** 页面。导航位置和中文名称可能随版本变化；若找不到入口，先确认客户端具备本地插件功能，参考[官方插件说明](https://learn.chatgpt.com/docs/plugins)，不要在浏览器寻找电脑文件登记。
3. 在插件目录的**来源选择器／来源标签**中切换到安装器打印的本地来源。新建来源的显示名通常为 **Auto Prompt Local**，内部名称为 `auto-prompt-local`；已有目录自定义名称时以安装器和实际页面为准。这个来源是目录里的分类，不是让你打开一个 Windows 文件夹。
4. 在所选来源中找到 **Auto Prompt Skill**，打开详情并安装；已经安装旧内容时使用客户端实际提供的刷新或更新入口。按提示完成权限和启用步骤。
5. 新建连接本机执行环境的 Work 聊天，再调用技能。

如果页面只有公开插件、没有上述本地来源，确认安装器是在当前 Windows 用户目录运行，并刷新或重新启动桌面应用。程序来源为 `%USERPROFILE%\.codex\plugins\local-auto-prompt-skill`，个人目录登记为 `%USERPROFILE%\.agents\plugins\marketplace.json`；隔离安装的 `-HomeDirectory` 不会自动让真实用户客户端发现它。仍找不到时保留安装器摘要和客户端界面，按[常见问题](#常见问题)排查，不删除整个插件配置。

此路径不使用网页的“上传插件”，也不通过运行安装器把插件发布到公开目录。

新建连接本机的 Work 聊天，选择技能或发送：

~~~text
请调用 Auto Prompt 技能。
~~~

预期进入简短引导，而不是空模板。需要确认加载情况时，让它报告实际读取的 `SKILL.md` 路径和插件版本，应为 v1.1.0；完整检查见[新对话验收清单](chatgpt-acceptance.md)。

**安装器自检通过不代表客户端已经启用。** 同版本修订还需按[升级步骤](#升级与自定义内容)重新下载、安装和刷新，不能只看版本号或旧聊天的说法。

### 5. 提交第一条需求

在同一 ChatGPT 聊天框发送：

~~~text
目标 Agent：ChatGPT
需求：根据我提供的会议记录，整理决定、行动项及待确认信息。
约束：用中文，不推测缺失的负责人和截止时间。
~~~

自然语言默认灵活模式，预期得到可复制的提示词；有影响结果的关键歧义时先回答澄清问题。之后可说“追加……”“替换……”或“撤销刚才修改”；“直接使用”只结束转换，不执行业务任务。

需要固定输出时明确选择严格模式。确定性边界、旧 JSON 默认值和语言限制见[首页模式说明](../README.md#灵活模式与严格模式)和[输入参考](../skills/auto-prompt/references/input.md)。

## 升级与自定义内容

### 网页个人导入

网页导入与本地来源独立：重新运行 Windows 安装器不会更新网页个人条目。下载需要的 `plugin.zip` 和对应校验清单，在网页“个人 → 我创建的”打开已有 Auto Prompt 条目，检查详情或 `…` 菜单实际提供的编辑／更新入口。

同名 ZIP 的覆盖更新、重复导入或网页回滚尚未验证；不要把再次“上传插件”视为已经确认的原条目升级，也不要为升级先删除原插件。若界面没有明确更新入口，先记录当前条目和要求的操作，再确认处理方式。相同版本号也可能对应不同分发内容。

### 桌面本地更新

**升级到 v1.1.0：** 重新下载上面的整合包及校验清单，校验后运行安装器，再刷新客户端插件。升级前关闭相关编辑器；安装器保留独立自定义文件，已修改的程序文件仍会报告冲突。已登记的旧 Python 不符合[补丁策略](security-maintenance.md#运行时维护)时，安装器自动准备专属 Python 3.13.16；离线升级必须提供新版校验 ZIP 或兼容解释器，不能使用旧运行时 ZIP。详见[v1.1.0 发布说明](release-v1.1.0.md)。

**历史 v1.0.2 有同版本修订。** 已安装 1.0.2 的用户也需重新下载整合包和 `SHA256SUMS.txt`，核对校验值，运行 `Install-Windows.cmd` 并刷新客户端；程序文件归属按内容摘要判断，不只比较版本号。

若客户端仍使用旧缓存，应通过客户端支持的本插件刷新/重装入口重新加载，不删除整个插件缓存。[发布说明](release-v1.0.2.md)记录修订来源；重写前旧提交需按[历史映射](history-rewrite.md)定位当前对象，不保证旧 SHA 可在新克隆检出。

关闭正在使用旧技能的聊天后，解压新包，运行同一入口。程序更新和用户配置分开处理：

- 旧版 v1.0.0 用已审计的分发文件摘要识别；新安装用 `.auto-prompt-install.json` 记录程序文件归属。
- 未修改的程序文件替换为新版；独立用户文件复制到新来源目录，内容不变。
- 修改过或删掉的程序文件、新版路径与用户文件冲突、重复/不同来源条目、未知配置形状均停止并说明问题。
- marketplace 的原名称、其他条目和本项目非 source 自定义字段保留，不拼接 JSON 文本。
- 将自定义规则存入单独的 user/ 或其他独立文件便于保存。保存并不代表自动应用；使用时明确引用。不要把机器配置或个人偏好提交到公开仓库。

遇到程序文件冲突：先单独保留你的修改并对比原版；由你决定迁入独立文件还是修改程序。将程序文件恢复为已识别的原分发版本后重试。不要删除归属清单来强制覆盖。安装器没有忽略冲突的 force 模式。

## 离线与显式运行时

本节及后续事务回滚、项目专属路径和隔离安装仅适用于桌面本地路径。

以下命令在解压文件夹的 PowerShell 中运行。把示例路径替换为实际路径；若执行策略阻止直接运行脚本，使用首次安装中的 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File` 方式，并在末尾加对应参数。

~~~powershell
# 指定已有解释器；不兼容时自动准备专属版本，而不替换这个解释器
.\Install-Windows.ps1 -PythonPath 'C:\path\to\python.exe'

# 不复用共享解释器，准备专属运行时
.\Install-Windows.ps1 -DedicatedRuntime

# 在联网电脑取得官方文件后，复制到新电脑离线使用
.\Install-Windows.ps1 -DedicatedRuntime -Offline -RuntimeArchive 'C:\downloads\python-3.13.16-embed-amd64.zip'
~~~

固定 URL 和完整 SHA-256 记录在 [scripts/runtime-lock.json](../scripts/runtime-lock.json)；预先提供的 ZIP 仍必须校验。可从 Python 官方版本页下载相同文件，不修改 lock 来绕过校验。已兼容的运行时优先复用，`-RuntimeArchive` 仅在需要准备运行时时读取。

官方 ZIP 来自 [Python 3.13.16 发布页](https://www.python.org/downloads/release/python-31316/)的 **Windows embeddable package (64-bit)**，不是普通安装器；文件名为 `python-3.13.16-embed-amd64.zip`。大小、联网和许可方案比较见[依赖设计说明](v1.0.1-design.md)。

## 失败与回滚

### 安装失败

可捕获的失败仅恢复本次尝试写入的资源；未写入的共享登记保持现状。恢复前校验备份和当前内容；若本次写入后又被外部修改，保留该修改并报告 `recovery_conflict` 与事务 ID，其他仍可安全恢复的资源先恢复。关闭其他插件管理器后再处理冲突；摘要检查不是全系统排他锁。下载的新专属 Python 可保留为未引用文件，旧运行时与共享依赖不被删除。事务目录保留证据与旧文件，便于人工恢复。

### 恢复过程的保护措施

2026-10-07 恢复修订：共享登记和运行时指针以原子替换恢复，避免复制中断留下半份 JSON。

v1.1.0 安全修订在旧目录移入 `displaced` 后再次检查内容；并发编辑或无法读取时恢复最新目录（活动位置仍空缺时），停止安装并报告事务 ID。若活动位置已有其他内容则保留双方证据，不强行覆盖。检查相关目录、关闭编辑器后重试，不对冲突事务强制回滚；详见[保护范围](security-maintenance.md#输入与文件保护)。

目录恢复先在事务专属 `restore-stage` 中复制并校验旧文件；复制失败时当前程序目录仍保留。`restore.json` 记录准备阶段和摘要，切换时将当前目录保留在 `restore-displaced`。

恢复再次中断时，使用修订安装器和同一事务 ID 重试；仅在备份、准备目录、移开目录及登记证据一致时继续，不覆盖之后的用户改动。

旧 schema 1 事务仍可读取；旧安装器已经留下的无证据缺失或部分复制状态仍需人工对比，不能凭目录缺失强行恢复。

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

修订安装器还支持有 `restore.json` 与完整 `restore-stage`／`restore-displaced` 证据的恢复切换中断，包括已提交安装的回滚。仅目录缺失或中间证据遭修改都不能作为自动恢复依据。新安装器仍可读取 v1.0.1 的 schema 1 事务；旧安装器不认识新增恢复证据，不要用旧安装器继续新修订的中断回滚。人工改动过的中间态需对比处理。

真实断电及文件系统损坏未验收，不能将进程中断测试当作断电恢复保证。

回滚后在 ChatGPT 刷新/重新安装本项目插件并新建聊天，确认加载旧版本。宿主管理的缓存不是安装器的事务对象。

## 常见问题

### 网页路径

- 找不到“上传插件”：入口受账号、工作区和功能权限影响，不能凭公共插件页推断具备导入权限。
- 选了错误文件：网页入口使用 `auto-prompt-skill-1.1.0-plugin.zip`，保持 ZIP。单技能包缺少插件清单，桌面整合包包含额外安装材料；按推荐文件重新选择。
- 导入后找不到：确认登录同一账号／工作区，切换到“个人 → 我创建的”，打开条目检查安装状态，再新建聊天用 `@` 搜索。
- 上传出现格式或规则错误：保留错误全文或截图，先核对校验值与文件名；包结构和账号检查通过后再处理具体问题，不凭“上传入口可见”宣称导入一定成功。
- 能生成提示词但严格模式无法运行：按[严格模式环境检查](#6-严格模式先检查执行环境)区分工具缺失、原文件不可访问和运行时不符合策略。网页 ZIP 不准备解释器，Windows 安装器也不会自动修复云端 Python；受阻时选择灵活模式或已验收的桌面本地路径，不冒称严格成功。
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
