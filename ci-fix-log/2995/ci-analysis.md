# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, No such file or directory, ^M, bwa_test.sh, check test failed

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `eulerpublisher` 包内置测试脚本 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施文件，非 PR 变更内容）
- 失败原因: `bwa_test.sh` 脚本文件使用了 Windows/DOS 风格的 CRLF (`\r\n`) 换行符，导致 shebang 行 `#!/bin/sh` 末尾携带不可见的回车符 `\r`，内核尝试查找解释器 `/bin/sh\r`（即 `/bin/sh` + `^M`），该文件不存在，脚本无法执行。

### 与 PR 变更的关联

**与 PR 变更无关。** PR 变更仅包含：
1. 新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` — Docker 镜像构建成功（`#7 DONE 199.0s`），编译、打包、推送均无错误
2. 更新 README.md、image-info.yml、meta.yml — 均为元数据/文档修改

CI 失败发生在构建和推送成功之后的 `[Check]` 测试阶段（`eulerpublisher` 工具内部调用 `bwa_test.sh`），失败的根因是 CI 基础设施中 `eulerpublisher` 包自带的 `bwa_test.sh` 脚本文件包含 CRLF 换行符。PR 的 Dockerfile 及所有变更本身没有引入任何错误。

## 修复方向

### 方向 1（置信度: 高）
这不是 PR 代码层面的问题，无需修改 Dockerfile 或 PR 中的任何文件。问题出在 CI 基础设施层 — `eulerpublisher` Python 包的测试脚本 `bwa_test.sh` 被以 Windows 换行格式（CRLF）打包/部署到了 CI runner 上。修复方式是在 `eulerpublisher` 包中重新生成或转换该文件为 LF 格式（如通过 `dos2unix` 或在 git 中设置 `core.autocrlf`），然后更新 CI runner 上的 `eulerpublisher` 包版本。该修复不在本次 PR 范围内，应由 CI 基础设施维护者处理。

## 需要进一步确认的点
- `eulerpublisher` 包中 `bwa_test.sh` 的具体来源：是包发布时打包进去的，还是在 CI 运行时从某个仓库拉取的？需要确认其打包/部署流程中的换行符处理。
- 同一 CI 节点上其他镜像（如 `bwa 0.7.18-oe2203sp3`）的 check 测试是否也已存在同样的问题，只是之前未被触发（因为之前没有 bwa 镜像的 PR 变更触发该 check 步骤）。
- `bwa_test.sh` 脚本的内容：假设换行符问题修复后，脚本本身是否能正确测试 bwa 容器（即脚本逻辑本身是否有效），日志中仅有 shebang 解析失败错误，无法判断脚本内容是否正确。

## 修复验证要求
不涉及正则 patch 外部源文件，无需额外验证。
