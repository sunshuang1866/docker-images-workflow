# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需代码修改。

## 修改的文件
无。CI 失败与 PR 变更的文件无关，无需修改任何源代码。

## 修复逻辑
CI 失败分析报告明确指出：失败类型为 `infra-error`，根因是 eulerpublisher CI 工具内置测试脚本 `/usr/local/etc/eulerpublisher/tests/container/app/bwa_test.sh` 使用了 Windows 风格的 CRLF 换行符，导致 shebang 解释器路径被解析为 `/bin/sh\r`（而非 `/bin/sh`），触发 `bad interpreter: No such file or directory` 错误。

该测试脚本位于 eulerpublisher 安装包内，不在本仓库中，且与本次 PR 新增的 Dockerfile（已使用 Unix LF 换行符）及元数据文件（README.md、image-info.yml、meta.yml）完全无关。Docker 镜像的构建和推送均已成功完成，失败仅发生在 CI 工具的测试环节。

应由 CI 运维人员检查 eulerpublisher 安装包中该测试脚本的换行符格式，使用 `dos2unix` 或 `sed -i 's/\r$//'` 将 CRLF 转换为 LF 后重新部署。

## 潜在风险
无。未对仓库代码做任何修改。