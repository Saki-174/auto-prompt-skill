# 安装与使用 · v1.1.1

> v1.1.1 安全性修复版：升级和回滚保留 Windows 访问权限，保护备份与临时文件。变更与升级限制见[发布说明](releases/v1.1.1.md)。

先核对正在使用的安装包版本和校验值，再按对应步骤操作。[GitHub 文档](https://github.com/Saki-174/auto-prompt-skill/blob/main/docs/install.md)可能先于 Release 更新，不能据此认定已下载包包含相同文件；实际菜单以当前宿主为准。

本教程分成两条独立路径：**Windows 电脑浏览器中的 ChatGPT 网页版**，以及 **Windows x64 的 ChatGPT 桌面客户端本地 Work**。先选环境，再下载对应文件；它们不共用安装步骤。

[返回首页](../README.md) · [网页版安装](#一windows-电脑浏览器网页版安装) · [桌面本地安装](#二windows-桌面客户端本地安装) · [升级](maintenance.md#升级与自定义内容) · [回滚](maintenance.md#失败与回滚) · [常见问题](maintenance.md#常见问题) · [卸载](maintenance.md#卸载)

## 先选环境与文件

| 你要在哪里使用 | 应下载的文件 | 接下来做什么 |
| --- | --- | --- |
| 浏览器中的 ChatGPT 网页版 | `auto-prompt-skill-1.1.1-plugin.zip` | 保持压缩状态，在网页插件页“上传插件” |
| ChatGPT Windows x64 桌面客户端的本地 Work | `auto-prompt-skill-1.1.1-bundle.zip` | 解压，运行 Windows 安装器，再在客户端启用 |

另有 `auto-prompt-1.1.1-skill.zip`，用于已有单技能导入／发现方式的宿主；本教程的网页“上传插件”和桌面安装器路径均使用上表文件。GitHub 的 **Source code** 压缩包也不是这两条路径的推荐下载项。

所有文件均在 [v1.1.1 发布页](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.1.1)的 **Assets** 中，校验清单是 [SHA256SUMS.txt](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.1/SHA256SUMS.txt)。两条路径都需要可登录的 ChatGPT 账号和相应插件入口，账号或工作区政策可能限制可见功能。

## 一、Windows 电脑浏览器：网页版安装

适合主要在浏览器使用 ChatGPT、希望进行日常灵活改写的场景。以下步骤说明网页上传入口，不构成“无需本机安装器或 Python”的验证；网页依赖条件和脚本执行能力尚需在隔离环境中确认。

### 1. 下载网页插件包

1. 在 Windows 浏览器打开 [v1.1.1 发布页](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.1.1)。
2. 展开 **Assets**，下载 [auto-prompt-skill-1.1.1-plugin.zip](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.1/auto-prompt-skill-1.1.1-plugin.zip) 和 `SHA256SUMS.txt` 到同一下载文件夹。
3. 在该文件夹打开 PowerShell，用以下只读命令核对文件：

~~~powershell
Get-FileHash -LiteralPath '.\auto-prompt-skill-1.1.1-plugin.zip' -Algorithm SHA256
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

1. 在文件选择框中选中刚下载的 `auto-prompt-skill-1.1.1-plugin.zip`。
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

无需提前安装 Python。安装器会复用符合[维护策略](security-maintenance.md#运行时维护)的 Python；找不到时，从 Python 官方下载固定的 3.13.16 Windows x64 嵌入式运行时，校验后放入项目专属目录。首次下载约 10.9 MB，需要联网；有兼容解释器或已校验的官方 ZIP 时可[离线安装](maintenance.md#离线与显式运行时)。

自动依赖准备仅限 Windows x64。其他平台保留[手动兼容路径](maintenance.md#手动兼容路径)，不等于已完成其他宿主或平台的客户端验收。本地安装不会自动同步到网页、移动端或云端；严格脚本能离线运行，ChatGPT 对话仍由宿主服务提供。

### 2. 下载并核对文件

打开 [v1.1.1 发布页](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.1.1)，展开 **Assets**，下载这两个文件到同一文件夹：

- [auto-prompt-skill-1.1.1-bundle.zip](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.1/auto-prompt-skill-1.1.1-bundle.zip)：含安装器、技能、脚本及文档。
- [SHA256SUMS.txt](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.1/SHA256SUMS.txt)：三个 ZIP 的校验清单。

**桌面本地安装使用整合包。** 上面的网页路径使用 `plugin.zip`；`skill.zip` 用于已有单技能导入方式。它们不含本地安装器；GitHub 的 **Source code** 压缩包也不是推荐下载项。

在下载文件夹打开 PowerShell，运行以下只读命令：

~~~powershell
Get-FileHash -LiteralPath '.\auto-prompt-skill-1.1.1-bundle.zip' -Algorithm SHA256
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

安装器实际运行已安装的严格启动器并核对固定输出；失败时不报告成功。遇到错误先阅读提示和[常见问题](maintenance.md#常见问题)，不要跳过自检。

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

如果页面只有公开插件、没有上述本地来源，确认安装器是在当前 Windows 用户目录运行，并刷新或重新启动桌面应用。程序来源为 `%USERPROFILE%\.codex\plugins\local-auto-prompt-skill`，个人目录登记为 `%USERPROFILE%\.agents\plugins\marketplace.json`；隔离安装的 `-HomeDirectory` 不会自动让真实用户客户端发现它。仍找不到时保留安装器摘要和客户端界面，按[常见问题](maintenance.md#常见问题)排查，不删除整个插件配置。

此路径不使用网页的“上传插件”，也不通过运行安装器把插件发布到公开目录。

新建连接本机的 Work 聊天，选择技能或发送：

~~~text
请调用 Auto Prompt 技能。
~~~

预期进入简短引导，而不是空模板。需要确认加载情况时，让它报告实际读取的 `SKILL.md` 路径和插件版本，应为 v1.1.1；完整检查见[新对话验收清单](chatgpt-acceptance.md)。

**安装器自检通过不代表客户端已经启用。** 同版本修订还需按[升级步骤](maintenance.md#升级与自定义内容)重新下载、安装和刷新，不能只看版本号或旧聊天的说法。

### 5. 提交第一条需求

在同一 ChatGPT 聊天框发送：

~~~text
目标 Agent：ChatGPT
需求：根据我提供的会议记录，整理决定、行动项及待确认信息。
约束：用中文，不推测缺失的负责人和截止时间。
~~~

自然语言默认灵活模式，预期得到可复制的提示词；有影响结果的关键歧义时先回答澄清问题。之后可说“追加……”“替换……”或“撤销刚才修改”；“直接使用”只结束转换，不执行业务任务。

需要固定输出时明确选择严格模式。确定性边界、旧 JSON 默认值和语言限制见[首页模式说明](../README.md#灵活模式与严格模式)和[输入参考](../skills/auto-prompt/references/input.md)。

## 安装后的维护

升级、离线运行时、回滚、常见问题、卸载和手动路径统一见[维护说明](maintenance.md)。以下保留旧链接的章节入口；完整操作步骤仅维护一份。

## 升级与自定义内容

[阅读操作步骤](maintenance.md#升级与自定义内容)。

### 网页个人导入

[阅读操作步骤](maintenance.md#网页个人导入)。

### 桌面本地更新

[阅读操作步骤](maintenance.md#桌面本地更新)。

## 离线与显式运行时

[阅读操作步骤](maintenance.md#离线与显式运行时)。

## 失败与回滚

[阅读操作步骤](maintenance.md#失败与回滚)。

### 安装失败

[阅读操作步骤](maintenance.md#安装失败)。

### 恢复过程的保护措施

[阅读操作步骤](maintenance.md#恢复过程的保护措施)。

### 使用事务 ID 回滚

[阅读操作步骤](maintenance.md#使用事务-id-回滚)。

### 安装进程被强制结束

[阅读操作步骤](maintenance.md#安装进程被强制结束)。

## 常见问题

[阅读操作步骤](maintenance.md#常见问题)。

### 网页路径

[阅读操作步骤](maintenance.md#网页路径)。

### 桌面本地路径

[阅读操作步骤](maintenance.md#桌面本地路径)。

## 卸载

[阅读操作步骤](maintenance.md#卸载)。

### 网页个人导入

[阅读操作步骤](maintenance.md#网页个人导入)。

### 桌面本地路径

[阅读操作步骤](maintenance.md#桌面本地路径)。

## 项目专属路径

[阅读操作步骤](maintenance.md#项目专属路径)。

## 隔离验收，不影响实际用户配置

[阅读操作步骤](maintenance.md#隔离验收不影响实际用户配置)。

## 手动兼容路径

[阅读操作步骤](maintenance.md#手动兼容路径)。
