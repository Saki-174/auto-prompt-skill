# 历史重写与验证定位 · 2026-10-08

提交和注释标签的身份字段已改为 GitHub noreply，`main`、`v1.0.1`、`v1.0.2` 的本地和远端引用已更新。`v1.0.0` 不变。该操作没有改变文件树、提交说明、时间、作者名称、标签名称或 Release 附件，与后续 v1.1.0 安全性修复发布相互独立。

安全修订前的开发基线为 `5778b49f68cceff1116feaae915f2034818f710f`。以下对应关系区分历史审查定位与新克隆可解析的对象；旧 SHA 仅用于追溯，不作为当前安装入口或当前基线链接。

## 提交映射

| 重写前 SHA | 重写后 SHA（当前定位） |
| --- | --- |
| `78b9b835d336bfc0f04483d49e4417ba7f806e48` | [41fbe57851e2fd49f2759e74198bed6b2a14b3df](https://github.com/Saki-174/auto-prompt-skill/commit/41fbe57851e2fd49f2759e74198bed6b2a14b3df) |
| `cb1876e1172bd726a55be5547b3d41510add34b8` | [5257a3db05d2fa36d6a8993dfa0422cf9dfe1a80](https://github.com/Saki-174/auto-prompt-skill/commit/5257a3db05d2fa36d6a8993dfa0422cf9dfe1a80) |
| `f270409b95838405e7ffbc9da5f527f784eaa2d2` | [280748a072e4db8f3e67c7524e29ead95af77b83](https://github.com/Saki-174/auto-prompt-skill/commit/280748a072e4db8f3e67c7524e29ead95af77b83) |
| `78e0f0a4761526f871dade34223e5147de53da54` | [72fc08593660828b816f73b93754177fe2124e46](https://github.com/Saki-174/auto-prompt-skill/commit/72fc08593660828b816f73b93754177fe2124e46) |
| `4c4df30877d10aab6f6e1253e99f88bddf80e8ad` | [854b09882ff16f6ae6fa8c4b0882e104c594cb6c](https://github.com/Saki-174/auto-prompt-skill/commit/854b09882ff16f6ae6fa8c4b0882e104c594cb6c) |
| `08bc632026ec4e31dcffe07fc18c726f2fe37133` | [fab8191a3fa44b96e9dafc7acc8f1875d328b31d](https://github.com/Saki-174/auto-prompt-skill/commit/fab8191a3fa44b96e9dafc7acc8f1875d328b31d) |
| `44f31a04b09f01278d6ed671a2b0ed5397e55a28` | [5778b49f68cceff1116feaae915f2034818f710f](https://github.com/Saki-174/auto-prompt-skill/commit/5778b49f68cceff1116feaae915f2034818f710f) |

根提交 `41c9f0e5a2dc820efcfea1dc0a14a92f8712aa55` 没有变化。历史验收结果仍描述当时实际执行的代码和环境；文件树相同不能代替新候选的构建或测试。

## 标签对象映射

| 标签名称 | 旧注释标签对象 | 新注释标签对象 |
| --- | --- | --- |
| `v1.0.1` | `1eac3067f8991ca2a0d6eac8afd57d22d570b090` | `558f627b8d732eaac2cf6a7086bfb9ae5a21e97e` |
| `v1.0.2` | `8b24ec2da0b8985cca85d29fa9ae2d443dd42fd2` | `3a6e1654e0b4ec920d76148d87fb125d02a1c290` |

标签名称和 Release 附件不变；自动生成的 Source code 压缩包来自对应的新 Git 对象。附件中旧文档的 SHA 属于重写前记录，当前定位以上表为准。

## 新克隆与旧工作区

在新克隆的根目录可用以下只读命令核对定位：

```sh
git show --no-patch --format='%H %T' 5778b49f68cceff1116feaae915f2034818f710f
git show --no-patch --format='%H %T' 5257a3db05d2fa36d6a8993dfa0422cf9dfe1a80
git rev-parse v1.0.1 v1.0.2
```

旧工作区应先备份未提交文件和未跟踪内容，再在另一空目录重新克隆，按文件差异迁移自己的修改。不要把旧历史合并回新 `main` 或强推旧标签。在准备新目录的上一级终端运行：

```sh
git clone https://github.com/Saki-174/auto-prompt-skill.git auto-prompt-skill-clean
```

不要为同步历史删除整个客户端配置或共享依赖。受治理的项目记忆和旧审查日志保留其历史日期；如需更新另走对应流程。

## 公开旧入口仍未闭环

2026-10-08 的匿名复查中，两个旧提交的 patch 入口仍返回 HTTP 200，并含非 noreply 作者邮箱。当前 refs 已清理不表示 GitHub 旧对象、缓存或已被下载的副本消失；本页不展示旧邮箱，也不将其视为登录凭据。

如需继续清理，应向 [GitHub Support](https://support.github.com/)提供仓库标识、首个改写提交和仍可访问的旧 SHA，申请评估缓存/旧对象处置。受理与处理范围由 GitHub 决定；提交申请不等于清理通过，处理后需匿名复查旧入口。依据：[GitHub 历史清理说明](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)。

本地私密恢复备份和旧克隆可能仍含旧身份信息；不要上传、共享或纳入安装包。本次发布接受这一已知残留，不再申请平台缓存清理；没有发送 Support 申请，也不宣称旧邮箱已经撤回。
