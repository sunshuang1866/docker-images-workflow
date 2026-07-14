# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: /bin/sh^M, bad interpreter, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI 工具 `eulerpublisher` 的内置测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（非 PR 代码文件）
- 失败原因: `bwa_test.sh` 文件使用 Windows 风格的 CRLF 行尾（`\r\n`），导致 shebang 行 `/bin/sh` 被解析为 `/bin/sh^M`（`^M` 即 `\r`），系统找不到名为 `/bin/sh\r` 的解释器，shell 执行失败。

### 与 PR 变更的关联
该失败与 PR 代码变更**完全无关**。Docker 镜像构建和推送均成功完成：
- 编译阶段（`yum install` + `make`）成功，历时约 199 秒
- 镜像构建成功导出并推送至 `openeulertest/bwa:0.7.18-oe2403sp4-x86_64`
- 构建日志中无任何编译错误，仅有 `bwt_gen.c` 中的两个 harmless 编译警告

失败发生在 CI 后处理阶段的 `[Check]` 步骤，由 `eulerpublisher` 工具调用其内置测试脚本 `bwa_test.sh` 时触发。该脚本不属于 PR 提交范围，其 CRLF 行尾是 CI 运行环境中 `eulerpublisher` 包自身的缺陷。

## 修复方向

### 方向 1（置信度: 高）
此失败为 CI 基础设施问题，非 PR 代码缺陷。需由 CI 维护者修复 `eulerpublisher` 包中 `bwa_test.sh` 的行尾格式，将 CRLF 转换为 LF：
```bash
sed -i 's/\r$//' /etc/eulerpublisher/tests/container/app/bwa_test.sh
```
或重新打包 `eulerpublisher`，确保所有测试脚本以 Unix 行尾（LF）分发。

PR #2995 的 Dockerfile 和其他代码变更本身无问题，无需修改。

## 需要进一步确认的点
- 确认 `eulerpublisher` 包中 `bwa_test.sh` 是否确实包含 CRLF 行尾（可通过 `file` 命令或 `cat -v` 验证）
- 确认其他镜像（如已有的 `bwa/0.7.18/22.03-lts-sp3`）的 CI 检查是否同样受此影响（若 `bwa_test.sh` 是 bwa 镜像共享的测试脚本，则所有 bwa 镜像的检查都应失败，可验证是否为近期才引入的回归）
