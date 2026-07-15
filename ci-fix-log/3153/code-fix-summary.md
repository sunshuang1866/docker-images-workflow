# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施误报（infra-error），CI 流水线的 appstore 发布规范预检对所有 PR 无差别执行，将文档类 PR 的 `README.md` 误判为需要审核的 appstore 发布文件。

## 修改的文件
无

## 修复逻辑
分析报告确认失败类型为 `infra-error`。PR #3153 仅修改了 `README.md`（更新基础镜像可用 tag 列表的文档），不涉及任何应用镜像发布所需的 Dockerfile、meta.yml 等文件。CI 的 `eulerpublisher/update/container/app/update.py` 中 appstore 路径校验将根目录文档文件纳入检查，但其路径格式不符合 appstore 预期路径模式，导致 `[Path Error] The expected path should be /README.md` 错误。

此问题根源在 CI 平台侧：appstore 预检应增加 PR 文件类型/路径过滤逻辑，当 PR 仅修改根级文档文件而未触及任何应用镜像目录时，应跳过检查。代码本身无任何问题，不应强行修改源码。

## 潜在风险
无