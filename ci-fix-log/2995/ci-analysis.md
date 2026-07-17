# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, /bin/sh^M, No such file or directory, bwa_test.sh, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包内测试脚本）
- 失败原因: eulerpublisher 包自带的 `bwa_test.sh` 测试脚本使用 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh\r` 中的 `\r` 被内核解释为解释器路径的一部分，系统找不到 `/bin/sh\r` 解释器，`[Check]` 阶段执行测试脚本失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 并更新了 README.md、image-info.yml、meta.yml 三个元数据文件。Docker 镜像构建（`[Build]`）和推送（`[Push]`）阶段均完全成功——日志显示所有 7 个 Docker 构建步骤（依赖安装 → 源码下载/编译 → 清理）均正常完成，镜像已成功推送到 registry。失败仅发生在 CI 框架层 `[Check]` 阶段的 eulerpublisher 测试脚本中，该脚本的 CRLF 行尾问题属于 eulerpublisher 打包缺陷，与本次 PR 的任何文件变更无关。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，需修复 eulerpublisher Python 包中 `tests/container/app/bwa_test.sh` 的换行符——将 CRLF（`\r\n`）转换为 LF（`\n`）。可在 eulerpublisher 包的构建/打包流程中执行 `dos2unix` 或在 CI 流水线中对该脚本进行预处理。**此修复不在当前 PR 仓库范围内，需由 eulerpublisher 维护者处理。**

## 需要进一步确认的点
1. eulerpublisher 包的版本——确认当前 CI 环境安装的 eulerpublisher 版本是否是最新版，或者该 `bwa_test.sh` 是否为最近版本引入的回归。
2. 其他同类镜像（如其他 HPC 应用）的测试脚本是否也存在相同的 CRLF 问题，以判断是单文件问题还是 eulerpublisher 打包流程的系统性问题。
3. 确认 CI 环境中 git 的 `core.autocrlf` 配置——如果将该测试脚本作为 eulerpublisher 仓库中的文件管理，需检查 git 是否在 checkout 时自动转换了换行符。

## 修复验证要求
不适用（本次失败为 infra-error，无需 code-fixer 修改 PR 代码）。
