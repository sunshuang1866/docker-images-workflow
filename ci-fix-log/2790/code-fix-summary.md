# 修复摘要

## 修复的问题
无需代码修改 — CI 失败属于基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无（未修改任何文件）

## 修复逻辑
CI 失败分析报告明确指出：PR #2790 仅修改了仓库根目录的文档文件 `README.md`（和 `README.en.md`），未涉及任何 Dockerfile、`meta.yml`、`image-info.yml` 或其他应用镜像构建/发布相关文件。CI 失败的原因是 Jenkins 流水线将纯文档修改的 PR 错误路由到了 appstore 发布规范校验 Job（`multiarch/openeuler/x86-64/openeuler-docker-images`），该 Job 按应用镜像路径规范校验 `README.md`，因路径不匹配而报错。

此为 CI 流水线路由配置问题，修复应在 Jenkins 流水线的 trigger 层添加过滤逻辑：当 PR 仅修改仓库根目录文档文件且不涉及任何应用镜像目录时，跳过 appstore 发布规范校验 Job。**PR 的代码变更本身完全正确，无需任何修改。**

## 潜在风险
无 — 此修复方向不涉及任何仓库内代码变更，对现有功能无影响。