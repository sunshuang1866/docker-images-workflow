# 修复摘要

## 修复的问题
CI 基础设施误报 —— Appstore 发布规范预检工具对纯文档类 PR 进行了不合理的路径校验拦截。PR 代码本身无任何问题，无需代码修改。

## 修改的文件
无代码修改。

## 修复逻辑
CI 失败分析报告明确将此失败归类为 `infra-error`（置信度：高）。PR #3153 仅修改了根目录下的 `README.md` 和 `README.en.md`（更新基础镜像可用 Tags 列表），不涉及任何 Dockerfile、`image-list.yml` 或应用镜像目录变更。CI 流水线中的 `eulerpublisher` 预检工具将 `README.md` 识别为变更文件后，因不符合 `{image-version}/{os-version}/Dockerfile` 的最小路径模式而报 `[Path Error]`。该检查设计用于应用镜像发布 PR，不应拦截仅修改根级文档的 PR。此问题属于 CI 流水线配置缺陷，需在 CI 侧为 `docs:` 前缀的 PR 添加跳过 Appstore 检查的规则，或人工关闭此 CI 检查结果并合并 PR。

## 潜在风险
无 —— PR 代码无需修改，无代码变更风险。