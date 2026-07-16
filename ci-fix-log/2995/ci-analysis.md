# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 测试基础设施中的 bwa 测试脚本）
- 失败原因: `bwa_test.sh` 测试脚本使用了 Windows 风格的 CRLF 行尾符（`\r\n`），导致 shebang 行 `#!/bin/sh\r` 被内核解析为解释器路径 `/bin/sh\r`（含字面量回车符），该路径不存在，触发 "bad interpreter: No such file or directory" 错误。

### 与 PR 变更的关联
**与 PR 无关。** PR 的 Docker 镜像构建全程成功：依赖安装（`yum install make gcc zlib-devel`）正常、bwa 源码下载解压成功、`make` 编译通过、二进制文件安装到位、构建工具清理完成，镜像推送（`[Push] finished`）也成功。失败发生在 CI 流水线的 `[Check]` 阶段，因 eulerpublisher 测试框架中的 `bwa_test.sh` 脚本自身携带 CRLF 行尾无法被 Shell 执行，属于 CI 基础设施问题，PR 作者无法通过修改 Dockerfile 或任何仓库内文件解决。

## 修复方向

### 方向 1（置信度: 高）
将 eulerpublisher 仓库（CI 工具本身）中 `tests/container/app/bwa_test.sh` 的行尾从 CRLF（Windows 风格）转换为 LF（Unix 风格）。可通过 `dos2unix` 命令或在编辑器中设置行尾格式为 LF 后重新提交该文件实现。此修复属于 CI 基础设施维护，与 PR #2995 的代码变更无关。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 在 eulerpublisher 仓库中的实际路径，以及该文件是否仅影响 bwa 镜像还是也影响其他镜像的测试。
- 确认 eulerpublisher 仓库的 CI/CD 流程是否有行尾自动检查（如 `.gitattributes` 中的 `* text=auto`）来防止此类问题再次发生。

## 修复验证要求
无需 PR 作者验证。此问题应由 CI 基础设施维护者在 eulerpublisher 仓库中修复 `bwa_test.sh` 的行尾格式后，重新触发 PR #2995 的 CI 流水线即可。
