# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, CRLF, bwa_test.sh, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 测试基础设施脚本，非 PR 变更文件）
- 失败原因: CI 测试框架 `eulerpublisher` 中的 `bwa_test.sh` 脚本文件包含 Windows 风格换行符（CRLF，`\r\n`），导致 shebang 行 `#!/bin/sh\r` 被解释为 `/bin/sh^M`，shell 无法找到该解释器，测试脚本在启动阶段即失败。

### 与 PR 变更的关联
PR 变更与本次失败**无关**：
- Docker 镜像**构建成功**（所有步骤完成，二进制编译通过，`[Build] finished`，`[Push] finished`，最终镜像成功推送到 `docker.io`）
- PR 仅新增了 Dockerfile、README.md、image-info.yml、meta.yml 四个文件，不包含 `bwa_test.sh`
- 失败发生在 CI 的 **[Check]** 阶段——即 `eulerpublisher` 工具调用 `bwa_test.sh` 对已构建镜像进行验证时，因测试脚本自身的行尾格式问题崩溃，而非被测试镜像存在问题

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施层面修复：将 `eulerpublisher` 包中 `tests/container/app/bwa_test.sh` 的换行符从 CRLF（`\r\n`）转换为 LF（`\n`）。可以在 CI 环境中使用 `dos2unix` 或 `sed -i 's/\r$//'` 对该文件进行预处理，或从上游 eulerpublisher 源码修复该文件后重新打包发布。

## 需要进一步确认的点
- `eulerpublisher` 包中 `bwa_test.sh` 的 CRLF 问题是仅当前版本存在，还是所有部署版本均受影响（即其他 PR 的 BWA 构建是否也会在 Check 阶段遇到相同错误）
- 该测试脚本的来源（是否为 eulerpublisher 安装包的一部分，或由 CI 流水线从某个外部仓库动态拉取）

## 修复验证要求
无需验证——此为 infra-error，与 PR 代码变更无关，Code Fixer 无需处理。
