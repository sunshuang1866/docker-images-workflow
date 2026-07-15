# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, /bin/sh^M

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（由 CI 框架 `eulerpublisher` 包提供）
- 失败原因: CI 测试脚本 `bwa_test.sh` 使用 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh` 末尾携带不可见的回车符 `\r`（日志中显示为 `^M`）。Linux 内核尝试定位 `/bin/sh\r` 作为脚本解释器，因该路径不存在而报 `bad interpreter`。

### 与 PR 变更的关联
与 PR 代码变更**无关**。PR 仅新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 并更新配套元数据文件（README.md、image-info.yml、meta.yml）——均未涉及 `bwa_test.sh` 测试脚本。Docker 镜像构建和推送流程均已成功完成（#7 DONE 199.0s，push 成功），仅失败于 CI 后置 [Check] 阶段调用 `eulerpublisher` 框架自带的测试脚本时触发 CRLF 解释器错误。

## 修复方向

### 方向 1（置信度: 高）
`eulerpublisher` 包的 `tests/container/app/bwa_test.sh` 文件需转换行尾格式（CRLF → LF）。可通过 `dos2unix` 或 `sed -i 's/\r$//'` 处理。此为 CI 基础设施包发布时的格式问题，需由 `eulerpublisher` 包维护者在打包/发布环节确保所有 Shell 脚本使用 Unix 换行符（LF）。Code Fixer 无需对当前 PR 做任何修改。

## 需要进一步确认的点
1. 确认 `eulerpublisher` 包中 `tests/container/app/bwa_test.sh` 的 CRLF 是来源仓库提交时即存在，还是在 CI 环境某中转环节被错误转换。
2. 确认同一 CI 环境中已存在的 bwa 22.03-lts-sp3 镜像在 [Check] 阶段是否也因同一脚本而失败，以判断是单文件问题还是整个 `eulerpublisher` 测试脚本集的行尾问题。
