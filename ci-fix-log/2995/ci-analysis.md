# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾符
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具包内的测试脚本）
- 失败原因: `bwa_test.sh` 测试脚本文件包含 Windows 风格的 CRLF（`\r\n`）行尾符。shebang 行 `#!/bin/sh` 末尾的 `\r` 被 Linux 内核认为是解释器路径的一部分，试图查找 `/bin/sh^M` 这个不存在的文件，导致 "bad interpreter" 错误。

### 与 PR 变更的关联

**与 PR 无关。** PR 的改动（新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`、更新 README.md、image-info.yml、meta.yml）均正常通过。日志显示 Docker 镜像构建完全成功：

- Docker build 所有步骤均 `DONE`：基础镜像拉取成功、`yum install` 依赖安装成功（17 个包）、bwa 源码编译成功、构建工具清理成功
- `[Build] finished` 和 `[Push] finished` 日志确认构建与推送阶段均已通过
- 失败仅发生在 CI eulerpublisher 工具链的 `[Check]` 阶段，原因是 `eulerpublisher` 包自带的 `bwa_test.sh` 测试脚本本身具有 CRLF 行尾符问题

## 修复方向

### 方向 1（置信度: 高）
`eulerpublisher` 工具包中的 `bwa_test.sh` 文件存在 Windows CRLF 行尾符，需要将文件换行符转换为 Unix LF（`\n`）格式。这属于 CI 基础设施问题，应在 `eulerpublisher` 包仓库中修复该测试脚本的行尾符，或在 CI 编排步骤中对测试脚本执行 `dos2unix` / `sed -i 's/\r//'` 转换后再执行。PR 本身的代码无需任何修改。

## 需要进一步确认的点

1. 确认 `eulerpublisher` 包中 `tests/container/app/bwa_test.sh` 的源文件是否确实包含 CRLF 行尾符（可通过 `file` 命令或 `cat -A` 验证）
2. 确认同一批 CI runner 上其他镜像的测试脚本是否也存在类似问题，或仅有 `bwa_test.sh` 受影响
3. 确认该 `bwa_test.sh` 是否是新近加入 eulerpublisher 包的文件（即是否由某次合入引入了 CRLF 行尾符），以便从源头修复而非仅做 CI 层面的绕过
