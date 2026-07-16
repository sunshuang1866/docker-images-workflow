# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error），根因是 CI 编排脚本 `update.py` 对纯文档类 PR 未做豁免，导致不相关的 appstore 发布规范校验被错误触发。

## 修改的文件
无（PR 变更的 `README.md` 内容本身正确，无需修改）

## 修复逻辑
CI 分析报告明确指出：
- 失败类型为 `infra-error`，置信度高
- PR #2790 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`，更新可用镜像 Tags 列表，属于正确的文档维护操作
- "本次 PR 变更与 CI 失败无关" — 失败原因是 CI 流水线配置问题，应在 `eulerpublisher/update/container/app/update.py` 的触发条件中增加文档变更豁免逻辑
- "PR 代码本身无需任何修改"

根据修复原则，infra-error 类型不应强行修改代码，本 PR 的 `README.md` 内容无需任何改动。

## 潜在风险
无 — 本次未修改任何代码文件。CI 基础设施层面的问题需要由运维/CI 团队在流水线配置中修复。