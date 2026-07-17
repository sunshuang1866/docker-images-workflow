# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施误报（infra-error）：appstore 发布规范检查器（`update.py`）将纯文档 PR 的 `README.md` 变更误判为镜像发布路径违规。

## 修改的文件
无（CI 基础设施问题，不应通过修改 PR 代码解决）

## 修复逻辑
CI 分析报告明确指出这是一个 infra-error，置信度为高。PR #3153 仅修改了仓库根目录的 `README.md`（更新基础镜像 tag 列表和下载链接），内容本身合法，与任何 Docker 镜像的构建和发布无关。失败由 CI 流水线中的 appstore 发布规范检查器（`eulerpublisher/update/container/app/update.py:273`）引起：该检查器未识别纯文档 PR，对所有变更文件一律执行镜像发布路径校验，导致根级 `README.md` 被标记为 `[Path Error]`。

此问题的正确修复方向是在 CI 流水线侧（`update.py`）增加文件类型判断逻辑，使纯文档变更跳过 appstore 路径校验。此举不在当前 PR 的代码范围内，不应对 `README.md` 做任何修改来绕过 CI 检查。

## 潜在风险
无（未修改任何代码）