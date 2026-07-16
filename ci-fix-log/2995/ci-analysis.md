# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施测试脚本）
- 失败原因: CI 基础设施中 `eulerpublisher` 包的 `bwa_test.sh` 测试脚本使用了 Windows 风格的换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh\r` 被内核解析为执行 `/bin/sh\r`（含回车符），报 "bad interpreter: No such file or directory"。Docker 镜像构建（Build）和推送（Push）均已成功完成，仅 [Check] 阶段的测试脚本执行失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 变更仅新增了 bwa 0.7.18 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。日志显示 Docker 镜像构建全流程成功：

- 依赖安装（make、gcc、zlib-devel）→ 成功
- 源码下载和编译（bwa 0.7.18）→ 成功（有 2 个无害的 GCC 编译警告，不影响构建）
- 镜像导出和推送 → 成功（`[Build] finished` + `[Push] finished`）
- 失败仅发生在 CI 工具 `eulerpublisher` 调用其自身 `bwa_test.sh` 进行容器验证时，该脚本具有 CRLF 换行符问题，属于 CI 基础设施缺陷。

## 修复方向

### 方向 1（置信度: 高）
由 CI 基础设施维护者将 `eulerpublisher` 包中的 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 脚本的换行符从 CRLF 转换为 LF（Unix 格式）。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理。此修复在 CI runner 环境层面完成，不涉及 PR 代码变更。

### 方向 2（置信度: 低）
若 `bwa_test.sh` 不存在且在 [Check] 阶段被动态生成，则生成该脚本的工具或模板本身存在 CRLF 问题。需追溯 `eulerpublisher` 源码中生成该测试脚本的逻辑，修复其换行符输出。

## 需要进一步确认的点

1. 确认 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 文件的实际内容（是否为模板自动生成还是预置文件）
2. 确认同一 CI runner 上其他同类 HPC 镜像（如已有 22.03-lts-sp3 版本的 bwa）的测试脚本是否存在相同 CRLF 问题，还是仅影响新增的 SP4 版本检查路径
3. 确认 `eulerpublisher` Python 包中测试脚本的打包和部署方式（是 pip install 时写入还是运行时动态生成）

## 附注

PR Dockerfile 末尾缺少换行符（diff 中显示 `\ No newline at end of file`），这是一个轻微的格式问题，不影响构建，但建议补充末尾空行以符合 POSIX 文本文件规范。
