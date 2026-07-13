# 修复摘要

## 修复的问题
无需代码修改。此 CI 失败为 `infra-error`，根因是 CI 基础设施中 `eulerpublisher` 包内置的 `bwa_test.sh` 脚本使用了 Windows 风格的 CRLF 行尾，导致 `#!/bin/sh\r` 解释器无法被识别。

## 修改的文件
无（infra-error，不在 PR 代码范围内）

## 修复逻辑
CI 分析报告明确指出：
- Docker 镜像构建（build + push）已完全成功
- 失败仅发生在 CI 的 `[Check]` 测试阶段，触发位置为 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因为该测试脚本携带 CRLF 行尾（`^M`），导致 shebang 行解析异常
- **与 PR 变更无关**：PR 仅新增了 Dockerfile、README.md 条目、image-info.yml 和 meta.yml，未修改任何 CI 测试脚本

此问题需要通过以下方式之一解决（需 CI 运维人员或 eulerpublisher 包维护者介入）：
1. 在 CI runner 环境上对 `bwa_test.sh` 执行 `dos2unix` 或 `sed -i 's/\r$//'` 修复行尾
2. 联系 eulerpublisher 包的维护者，在发布时确保所有测试脚本使用 Unix LF 行尾

## 潜在风险
无