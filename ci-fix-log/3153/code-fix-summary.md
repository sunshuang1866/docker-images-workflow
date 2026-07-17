# 修复摘要

## 修复的问题
无需代码修改 — CI 基础设施误报（infra-error）。

## 修改的文件
无。

## 修复逻辑
CI 失败根因为 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范预检工具对根目录 `README.md` 进行了路径校验，报告 `[Path Error] The expected path should be /README.md`。该工具的作用域应为应用镜像目录下的发布文件（Dockerfile、meta.yml 等），不应将仓库根目录的文档文件纳入校验范围。PR #3153 仅修改了 `README.md` 中的镜像 tags 列表，内容本身正确无误。

由于 `update.py`（CI 工具）不在 `pr.changed_files` 中，且 `README.md` 没有任何需要修复的问题，此 CI 失败属于基础设施/CI 工具层面的缺陷，应由 CI 团队在 `eulerpublisher` 仓库中修复路径校验逻辑（增加根目录文档文件的白名单/排除规则），而非在源码仓库中修改代码。

## 潜在风险
无 — 未对任何代码文件做修改。