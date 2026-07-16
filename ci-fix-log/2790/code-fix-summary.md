# 修复摘要

## 修复的问题
无需代码修改。CI appstore 发布规范检查（`update.py`）对纯文档 PR 误报路径校验失败，属于 CI 基础设施/配置问题，非 PR 代码缺陷。

## 修改的文件
- 无

## 修复逻辑
PR #2790 仅修改了根级 `README.md`（更新可用镜像 Tags 列表），不含任何 Dockerfile、meta.yml 等镜像构建相关文件。CI appstore 发布规范预检工具（`update.py:273`）的路径校验逻辑要求变更文件必须属于合法的应用镜像目录结构（如 `Category/ImageName/Version/OS-Version/Dockerfile`），根级 `README.md` 不满足该约束，因此报 `[Path Error]`。

这不是代码层面的 bug，`README.md` 的内容本身没有问题。根据 CI 分析报告方向 1，修复应在 CI Pipeline 触发条件中增加过滤逻辑：当 PR 仅包含非镜像目录下的文档文件（如根级 `README.md`）变更时，跳过 appstore 规范检查步骤。此改动需修改 Jenkins/CI 流水线配置或 `update.py` 的白名单规则，均不在本次 PR 的 `pr.changed_files` 范围内。

## 潜在风险
无（未修改任何代码）