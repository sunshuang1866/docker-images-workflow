# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施问题（infra-error）：appstore 预检流程被错误应用于 PR #3153（纯文档更新），不应由代码层面解决。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出此失败类型为 `infra-error`。PR #3153 仅修改了 `README.md` 和 `README.en.md` 中的基础镜像 Tags 列表描述，不涉及任何镜像构建文件（Dockerfile、meta.yml、image-info.yml 等）。CI 的 appstore 预检错误地将此纯文档变更纳入路径校验范围并报 `[Path Error] The expected path should be /README.md`，这与 README 文件内容无关，属于 CI 管线配置层面未对文档类 PR 添加白名单豁免的问题。

根据修复工程师的"禁止操作"规则：不应修改 CI 配置文件、不应强行修改与 CI 失败无关的代码、也不应修改 `pr.changed_files` 之外的任何文件。此问题应在 CI 管线配置中增加文档类 PR 豁免规则来解决，或直接重试 CI 流水线。

## 潜在风险
无