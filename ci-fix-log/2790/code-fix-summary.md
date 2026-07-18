# 修复摘要

## 修复的问题
CI 失败由 appstore 发布规范检查误触发于根级纯文档文件 `/README.md` 导致，属于 CI 基础设施问题，不涉及 README.md 代码缺陷。无需对源码做代码修改。

## 修改的文件
- 无代码修改。当前 `README.md` 中无分析报告提及的标签重复问题（已被先前 fix 提交清理）。

## 修复逻辑
CI 失败的直接原因是 `eulerpublisher/update/container/app/update.py` 中的 appstore 路径校验器对 PR 变更的所有文件进行路径模板匹配，根级 `README.md`（路径 `/README.md`）不符合 `{分类}/{镜像名}/{版本号}/{os-version}/Dockerfile` 的应用镜像路径模板，导致 `Path Error`。此失败与 README.md 内容无关，与 PR 仅修改根级文档文件的文件范围直接相关。

根本修复需在 `update.py` 中增加变更文件过滤逻辑，对非应用镜像目录下的文件（如项目根目录的 `README.md`、`README.en.md`）跳过 appstore 路径校验。但该文件不在本次 PR 允许修改的文件范围（`['README.md']`）内，且按照项目约束"不扩展范围"原则，不对其进行修改。

## 潜在风险
无。此 PR 为纯文档变更，不涉及任何应用镜像 Dockerfile、meta.yml 或 image-list.yml，合入后不会影响镜像构建或发布流程。CI 失败需由基础设施侧修复 `update.py` 的过滤逻辑来解决。