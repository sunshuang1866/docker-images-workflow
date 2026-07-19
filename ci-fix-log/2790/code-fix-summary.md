# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施误报（infra-error），eulerpublisher appstore 预检工具将仓库根级 `README.md` 误判为应用镜像 README 并进行路径格式校验，属于 CI 工具的 false positive。

## 修改的文件
无。PR #2790 仅更新了仓库主 README 中的 Tags 信息，变更内容本身正确，无需修改任何代码。

## 修复逻辑
CI 分析报告明确指出：仓库根目录的 `README.md` 是项目主文档，不应被纳入 appstore 路径规范检查范围。该 PR 的唯一变更是更新支持的镜像 Tags 列表，内容正确。此为 CI 基础设施问题（infra-error），需要 CI 维护方处理 eulerpublisher 预检工具的逻辑，使其跳过仓库根级文件的 appstore 路径校验。

## 潜在风险
无（未修改任何代码）。