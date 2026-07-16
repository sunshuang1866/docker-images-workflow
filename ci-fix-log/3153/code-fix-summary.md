# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：

1. **失败类型**：`infra-error`（CI 基础设施问题）
2. **根因**：CI appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py:273`）对仓库根目录下的 `README.md` 执行了不适用的路径校验。工具从 git diff 获取的路径为不带前导 `/` 的相对路径（`README.md`），但校验时期望的格式带前导 `/`（`/README.md`），导致字符串精确匹配失败。
3. **与 PR 变更的关系**：PR #3153 仅更新了 `README.md` 和 `README.en.md` 中基础镜像 tags 列表的文档内容，未修改任何 Dockerfile、构建脚本、镜像目录结构或 `image-list.yml`。CI 失败是工具本身的路径归一化不一致问题，与 PR 代码变更内容无关。

根据约束规则"如果分析报告指出是 infra-error（CI 基础设施问题），在 output_file 中说明无需代码修改，不要强行改代码"，本次不做任何源码修改。

## 潜在风险
无。该问题需要由 CI 工具维护方修复 `eulerpublisher` 中的路径归一化逻辑，或对根目录文档类文件（非镜像目录下的文件）豁免 appstore 路径校验。