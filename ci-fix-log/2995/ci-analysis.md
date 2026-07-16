# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, /bin/sh^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具 eulerpublisher 自带的测试脚本）
- 失败原因: `bwa_test.sh` 文件使用了 Windows 风格的 CRLF 行尾（`\r\n`），导致 shebang 行 `#!/bin/sh` 被解析为 `#!/bin/sh\r`（日志中显示为 `^M`），系统尝试查找名为 `/bin/sh\r` 的解释器失败，测试脚本无法执行。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了 BWA 0.7.18 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像构建和推送均成功完成（`#7 DONE 199.0s`，`[Build] finished`，`[Push] finished`），失败发生在 CI 工具 `eulerpublisher` 的 [Check] 后处理阶段——其自带的 `bwa_test.sh` 测试脚本因行尾格式问题无法被 Shell 解释执行。

## 修复方向

### 方向 1（置信度: 高）
此问题为 CI 基础设施问题，需修复 `eulerpublisher` 包中的 `tests/container/app/bwa_test.sh` 文件，将其行尾从 CRLF（`\r\n`）转换为 LF（`\n`）。这属于 CI 工具维护范畴，PR 作者无需修改任何代码。

### 方向 2（置信度: 低）
若 `bwa_test.sh` 实际上期望从 PR 仓库中获取（即需要 PR 作者在 Dockerfile 同级提供测试脚本），则 PR 新增的 `HPC/bwa/0.7.18/24.03-lts-sp4/` 目录下缺少 `bwa_test.sh`。但目前日志显示的路径指向系统安装的 eulerpublisher 目录，且同类已有版本（如 `22.03-lts-sp3`）的 CI 通过，说明更可能是 CI 工具的测试脚本文件本身被污染了 CRLF 行尾。

## 需要进一步确认的点
1. 确认 `eulerpublisher` 包中的 `tests/container/app/bwa_test.sh` 文件的 git 提交记录，排查 CRLF 是在何时被引入的（是否最近有 eulerpublisher 仓库的更新引入了此问题）。
2. 确认同类 PR（如其他新增 openEuler 24.03-LTS-SP4 镜像的 PR）是否也出现相同的 `^M` 和 `bad interpreter` 错误，以判断是否为 CI 环境的系统性故障。
3. 如果该测试脚本需要与 Dockerfile 一起提交，需确认 `HPC/bwa/0.7.18/22.03-lts-sp3/` 目录下是否已有 `bwa_test.sh` 文件，以及该文件是否也应复制到 `HPC/bwa/0.7.18/24.03-lts-sp4/`。

## 修复验证要求
无需验证。此问题属于 CI 基础设施问题（eulerpublisher 工具文件行尾格式），修复由 CI 维护者执行，不涉及 PR 代码变更。
