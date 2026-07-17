# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `infra-error`（CI 基础设施问题），根因是 `eulerpublisher` 包中的 `bwa_test.sh` 测试脚本包含 Windows 行尾（CRLF），导致 shebang 解释器查找失败（`/bin/sh^M: bad interpreter`）。

## 修改的文件
无。PR 提交的 4 个文件（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`、`HPC/bwa/README.md`、`HPC/bwa/doc/image-info.yml`、`HPC/bwa/meta.yml`）均内容正确，Docker 构建、镜像导出及推送阶段全部成功完成，无需任何修改。

## 修复逻辑
CI 分析报告将失败归类为 `infra-error`，置信度 **高**。失败的 [Check] 阶段发生在 `eulerpublisher` 包自带的测试脚本 `bwa_test.sh` 上，该脚本的 CRLF 行尾问题与本次 PR 的代码变更完全无关。按照工作流程对 `infra-error` 的处理规则：不强行修改代码，需由 CI 基础设施维护者修复 `eulerpublisher` 包。修复建议：将 `bwa_test.sh` 的行尾从 CRLF 转换为 LF（Unix），更新 `eulerpublisher` 包的源码仓库。

## 潜在风险
无