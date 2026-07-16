# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, /bin/sh^M, CRLF, bwa_test.sh

## 根因分析

### 直接错误
```
[Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: eulerpublisher CI 测试基础设施中的 `bwa_test.sh` 脚本
- 失败原因: CI 工具链内置的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF，即 `\r\n`），其 shebang 行 `#!/bin/sh\r\n` 在 Linux 上被解析为解释器 `/bin/sh\r`（带回车符），系统找不到该解释器，导致脚本无法执行。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了一个 Dockerfile 和配套元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像构建和推送均已成功完成（日志中可见 `#7 DONE 199.0s`、`#8 exporting to image`、`[Build] finished`、`[Push] finished`），失败发生在 CI 平台的后置检查阶段（`[Check]`），且失败的测试脚本位于 CI 系统安装的 `eulerpublisher` 包目录中（`/usr/local/etc/eulerpublisher/tests/container/app/bwa_test.sh`），与本次 PR 的文件变更完全无关。

## 修复方向

### 方向 1（置信度: 高）
修复 `eulerpublisher` 仓库中 `tests/container/app/bwa_test.sh` 文件的换行符格式，将 CRLF（`\r\n`）转换为 LF（`\n`）。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新提交到 eulerpublisher 仓库并发布新版本。Code Fixer 无需处理本 PR 的任何文件。

## 需要进一步确认的点
- 确认 eulerpublisher 仓库中 `bwa_test.sh` 的 Git 历史，核实 CRLF 问题是何时引入的（是否影响其他镜像的测试脚本）。
- 检查其他应用镜像的测试脚本（如 `*_test.sh`）是否也存在相同的 CRLF 问题，建议批量修复。
- 确认 CI 环境拉取的 eulerpublisher 版本，确保修复后的版本已部署到 CI runner。
