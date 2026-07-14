# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符错误
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施中的测试脚本）
- 失败原因: `bwa_test.sh` 脚本文件的 shebang 行（`#!/bin/sh`）被写入了 Windows 风格的 CRLF 换行符（`\r\n`），导致内核将解释器路径解析为 `/bin/sh\r`（末尾带 `\r`），无法找到该解释器，报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
本次 PR 的 Docker 镜像构建和推送均完全成功——日志中 `#7 DONE 199.0s`、`[Build] finished`、`[Push] finished` 均可证实。构建产出的镜像 `openeulertest/bwa:0.7.18-oe2403sp4-x86_64` 已成功推送到 registry。

失败发生在 CI 管线的 **`[Check]` 校验阶段**，该阶段调用 eulerpublisher 包内置的 `bwa_test.sh` 测试脚本对已构建镜像进行验收，但该脚本自身存在 Windows 换行符问题，导致脚本无法被 shell 执行。此问题与本次 PR 的 Dockerfile 及元数据变更**完全无关**，属于 CI 基础设施（eulerpublisher 测试套件）的预存缺陷。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需将 `bwa_test.sh` 文件的换行符从 CRLF（`\r\n`）转换为 LF（`\n`）。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该脚本。此修复应在 eulerpublisher 包或 CI runner 环境中进行，**与本次 PR 代码无关**。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 在 eulerpublisher 仓库中是否本身就带有 `\r` 换行符，还是仅在 CI runner 部署过程中被意外转换
- 确认其他镜像的对应测试脚本（如 `bwa_test.sh` 之外的其他 `*_test.sh`）是否也存在同样的 CRLF 问题
