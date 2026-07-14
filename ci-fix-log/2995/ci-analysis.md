# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: bad interpreter, ^M, /bin/sh^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher CI 工具链中的 bwa 容器测试脚本）
- 失败原因: `bwa_test.sh` 脚本文件含有 Windows 风格换行符（CRLF，`\r\n`），其 shebang 行 `#!/bin/sh` 末尾携带不可见的回车符 `\r`（日志中显示为 `^M`）。内核尝试以 `/bin/sh\r` 作为解释器执行该脚本，而系统不存在名为 `/bin/sh\r` 的二进制，导致 `bad interpreter` 错误。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #2995 仅提交了以下文件：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新增，19 行）
- `HPC/bwa/README.md`（新增一行标签文档）
- `HPC/bwa/doc/image-info.yml`（新增一条镜像信息）
- `HPC/bwa/meta.yml`（新增 `0.7.18-oe2403sp4` 条目）

Docker 镜像构建阶段 **完全成功**（`#7 DONE 199.0s`，编译通过，产物导出并推送成功）。失败发生在构建完成后 CI 工具链（eulerpublisher）的 `[Check]` 阶段——该阶段调用 eulerpublisher 仓库中预置的 `bwa_test.sh` 脚本来验证镜像功能，而该脚本文件本身存在 CRLF 换行符缺陷。此问题在 PR 提交前即已存在于 eulerpublisher 仓库中，本次 PR 仅是触发了该测试脚本被执行。

## 修复方向

### 方向 1（置信度: 高）
eulerpublisher 仓库中 `tests/container/app/bwa_test.sh` 脚本文件包含 Windows 风格 CRLF 换行符，需将其转换为 Unix 风格 LF 换行符。修复不在本次 PR 的代码范围内，应由 eulerpublisher 仓库维护者执行以下操作之一：
- 使用 `dos2unix` 工具转换：`dos2unix tests/container/app/bwa_test.sh`
- 使用 `sed` 去除回车符：`sed -i 's/\r$//' tests/container/app/bwa_test.sh`
- 在 eulerpublisher 仓库的 `.gitattributes` 中设置 `* text=auto` 或针对 `.sh` 文件强制 LF

## 需要进一步确认的点
1. **eulerpublisher 仓库克隆来源**：CI 日志中执行了 `Cloning into 'eulerpublisher'...`，需确认克隆的是哪个分支/版本，以及该脚本是否仅在特定分支存在 CRLF 问题。
2. **其他镜像是否受影响**：其他同样依赖 eulerpublisher 测试脚本的镜像（非 bwa 专用脚本可能也存在 CRLF 问题），建议排查 eulerpublisher `tests/container/app/` 目录下所有 `.sh` 文件的换行符格式。
3. **CI 节点 git autocrlf 配置**：确认 CI 构建节点的 git 全局配置中 `core.autocrlf` 是否为 `true`，如果是，可能在克隆时将 LF 自动转换为 CRLF，导致该问题。
