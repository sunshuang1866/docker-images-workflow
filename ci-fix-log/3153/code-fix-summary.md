# 修复摘要

## 修复的问题
无需代码修复 — CI 失败属于基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败根因是 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范预检工具对文件路径做了严格字符串匹配：检测到的 `README.md`（无前导 `/`）与期望的 `/README.md` 不匹配而导致检查失败。这是一个 CI 工具侧的路径格式匹配偏差（bug），并非 PR 文档内容变更引起。

PR 仅修改了 `README.md` 中的可用镜像 Tags 列表，属于纯文档更新，不涉及任何镜像构建逻辑或元数据。该 CI 失败需由 eulerpublisher 工具维护方修复（统一路径 normalize 或为根目录文档添加豁免规则），PR 作者侧无需也不应修改任何代码来绕过 CI 检查。

## 潜在风险
无