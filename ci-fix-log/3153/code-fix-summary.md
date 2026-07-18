# 修复摘要

## 修复的问题
无需代码修改 — 此为 CI 基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无（不需要修改任何源码文件）

## 修复逻辑
CI 失败根因是 eulerpublisher 工具在 appstore 发布规范预检阶段的路径比对逻辑存在格式偏差：工具将 git diff 产出的相对路径 `README.md` 与预期格式 `/README.md`（带前导 `/`）进行逐字匹配，因路径格式不一致误判为 `[Path Error]`。

PR #3153 仅修改了 `README.md` 和 `README.en.md` 两个纯文档文件（更新可用基础镜像 tags 列表），无任何 Dockerfile、meta.yml、image-list.yml 或应用镜像相关文件的变更。该 PR 原本不属于应用镜像上架范畴，不应受 appstore 规范的约束。

修复需在 eulerpublisher CI 工具侧（`eulerpublisher/update/container/app/update.py:273` 附近的 `check` 函数）实施：对路径比对逻辑增加 `os.path.normpath` 或前导 `/` 的标准化处理，消除格式偏差导致的误判。此改动不在本仓库代码范围内。

## 潜在风险
无 — 未对源码进行任何修改，不存在引入新问题的风险。