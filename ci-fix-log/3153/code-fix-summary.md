# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error：appstore 发布规范预检工具对纯文档 PR（仅修改 README.md）错误地执行了镜像路径校验。

## 修改的文件
无

## 修复逻辑
PR #3153 仅修改了 `README.md` 中的基础镜像 Tags 列表（文档更新），不涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 的变更，不是镜像发布 PR。失败原因在于 CI 流水线的 appstore 预检步骤未正确区分"文档 PR"与"镜像发布 PR"，对仓库根目录的 README.md 文件错误地执行了镜像路径校验。这是 CI 基础设施配置问题，需要 CI 侧增加判断逻辑：当 PR 仅包含文档文件变更时跳过 appstore 预检。代码层面无需任何修改。

## 潜在风险
无