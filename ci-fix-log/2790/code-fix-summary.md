# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error：CI 流水线的 appstore 发布规范预检工具（eulerpublisher/update.py）错误地将根目录 `README.md` 的变更判定为 "Path Error"，因为该检查期望所有变更文件符合 `{image-name}/{version}/{os-version}/` 目录层级，而根目录文档文件不符合该模式。

## 修改的文件
无

## 修复逻辑
根据 CI 分析报告，该失败属于 CI 基础设施问题（infra-error），与 PR #2790 的文档内容质量无关。PR 仅修改了根目录 `README.md`（文档更新），未包含任何 Dockerfile、meta.yml 或应用镜像相关变更。CI 工具的 appstore 预检对所有 PR 统一执行，当检测到根目录文档文件的变更时，无法将其映射到合法的 appstore 镜像发布路径，因此误报为路径错误。

**无需修改任何源代码。** 正确的修复方向是修改 CI 编排脚本（Jenkins pipeline 或 eulerpublisher 工具），在 appstore 预检阶段增加过滤逻辑：当 PR 仅变更根目录级项目文档（`README.md`、`README.en.md`、`LICENSE` 等非镜像文件）时，跳过该检查步骤。

## 潜在风险
无 — 未修改任何代码，不存在引入新问题的风险。