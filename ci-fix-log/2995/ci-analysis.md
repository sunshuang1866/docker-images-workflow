# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, /bin/sh^M, No such file or directory, CRLF

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: eulerpublisher CI 工具链中的测试脚本 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（等价于 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`）
- 失败原因: 该测试脚本使用了 Windows 风格的 CRLF 行尾符，导致 shebang 行被解析为 `#!/bin/sh^M`（而非 `#!/bin/sh`），内核无法找到名为 `/bin/sh^M` 的解释器，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
与 PR 代码变更**无关**。PR 提交的 Dockerfile（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`）已成功构建并推送（日志中明确显示 `[Build] finished` 和 `[Push] finished`），构建阶段的所有步骤（yum 安装依赖、下载源码、make 编译、镜像导出与推送）均正常完成。失败仅发生在 CI 流水线的 [Check] 阶段，该阶段调用 eulerpublisher 测试框架中的 `bwa_test.sh` 对构建产物进行验证，而该脚本自身因 CRLF 行尾问题无法被 shell 执行。

## 修复方向

### 方向 1（置信度: 高）
在 eulerpublisher 仓库中修复 `tests/container/app/bwa_test.sh` 的行尾格式，将 CRLF 转换为 LF。可使用 `dos2unix` 命令或编辑器的行尾转换功能处理该文件后重新发布 eulerpublisher 包。此修复不在当前 PR 的仓库范围内。

## 需要进一步确认的点
- 确认 eulerpublisher 仓库中 `tests/container/app/bwa_test.sh` 是否确实存在 CRLF 行尾问题（检查 git 历史中该文件是否被以 Windows 行尾提交）。
- 确认其他已有应用的测试脚本（如已有 image 的 `*_test.sh`）是否也存在相同的 CRLF 问题，还是仅 `bwa_test.sh` 新近引入。
- 如果 eulerpublisher 仓库中不存在该文件，需确认 CI 流程中 `bwa_test.sh` 的来源（是否由其他仓库/流程动态生成）。
