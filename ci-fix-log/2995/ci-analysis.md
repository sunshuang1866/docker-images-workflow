# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本行尾符错误
- 新模式症状关键词: `^M`, `bad interpreter`, `No such file or directory`, `bwa_test.sh`, `CRLF`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI Runner 上的 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包内测试脚本）
- 失败原因: eulerpublisher 包中分发的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh` 被解析为 `#!/bin/sh\r`。系统尝试以 `/bin/sh\r`（含回车符）为解释器执行脚本，因该路径不存在而报 `bad interpreter: No such file or directory`。

**关键事实**:
1. Docker 镜像构建完全成功 — 所有 yum 安装、curl 下载、`make` 编译、镜像导出与推送均正常完成（日志中 `[Build] finished` 和 `[Push] finished` 均出现）
2. 失败仅发生在 CI 流水线的 `[Check]` 阶段，即 `bwa_test.sh` 测试脚本被 Shell 加载执行时
3. `/bin/sh^M` 中的 `^M`（ASCII 0x0D / 回车符 `\r`）是 DOS/Windows 行尾符的典型标志

### 与 PR 变更的关联
**无关**。PR #2995 仅新增了一个 Dockerfile（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`）并更新了相关元数据文件（`README.md`、`image-info.yml`、`meta.yml`）。Dockerfile 中的构建逻辑完全正确，镜像已成功构建并推送至仓库。失败根因是 CI 基础设施中 eulerpublisher 包自带的测试脚本 `bwa_test.sh` 存在 Windows 换行符问题，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
修复 eulerpublisher 包中 `tests/container/app/bwa_test.sh` 的换行符，将 CRLF（`\r\n`）转换为 LF（`\n`）。此修复需在 eulerpublisher 仓库中进行，不在本 PR 的修改范围内。如果 CI 环境有临时修复权限，可在 CI runner 上执行 `dos2unix /etc/eulerpublisher/tests/container/app/bwa_test.sh` 或 `sed -i 's/\r$//' /etc/eulerpublisher/tests/container/app/bwa_test.sh` 作为应急方案。

## 需要进一步确认的点
1. eulerpublisher 包中 `bwa_test.sh` 是否是新近添加的文件（为支持 bwa 镜像检查而引入）？如果是新文件，确认 eulerpublisher 的打包/分发流程中 `.sh` 文件是否被错误地以 CRLF 格式保存或传输
2. 其他 CI runner 节点（如 aarch64、其他 x86-64 节点）上该文件是否也存在同样的换行符问题，还是仅当前特定 runner 上出现
3. 此 PR 之前是否有其他 bwa 版本的 CI 构建（如 `0.7.18-oe2203sp3`）也在同一 CI 环境中通过了 Check 阶段？若有，说明该测试脚本的换行符问题是近期引入的
