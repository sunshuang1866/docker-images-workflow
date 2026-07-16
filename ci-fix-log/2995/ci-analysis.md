# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, No such file or directory, ^M, /bin/sh^M

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包内的测试脚本）
- 失败原因: eulerpublisher CI 工具包中的 `bwa_test.sh` 测试脚本存在 Windows 风格换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh` 被内核解析为 `#!/bin/sh\r`（`^M` 为回车符的显示形式），内核找不到名为 `/bin/sh\r` 的解释器，报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile 构建流程全部成功：
- Docker 镜像构建成功（`[Build] finished`，所有 7 个 BuildKit 步骤均 DONE）
- 镜像推送成功（`[Push] finished`，manifest 已推送至 registry）
- bwa 源码编译成功（bwa 二进制已生成，链接无错误）

失败发生在 CI 后置检查阶段（`[Check]`），由 eulerpublisher 包内置的测试脚本 `bwa_test.sh` 的 CRLF 换行符问题触发，属于 CI 基础设施缺陷。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需修复 eulerpublisher 包中 `bwa_test.sh` 的换行符问题：将文件从 CRLF（`\r\n`）转换为 LF（`\n`），或重新打包/部署 eulerpublisher 时确保脚本文件以 Unix 换行符保存。此修复不涉及 PR #2995 的任何代码变更。

## 需要进一步确认的点
1. eulerpublisher 包中的 `bwa_test.sh` 是否为新近添加的文件（可能是在支持 bwa 24.03-lts-sp4 测试时引入的）
2. 同一 eulerpublisher 版本下的其他应用测试脚本（如 `*_test.sh`）是否也存在 CRLF 换行符问题
3. 该 CRLF 问题是 eulerpublisher 的打包/构建流水线引入，还是特定部署节点上的文件损坏
