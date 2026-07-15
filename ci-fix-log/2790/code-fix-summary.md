# 修复摘要

## 修复的问题
无需代码修改。CI 失败根因为 `infra-error`：appstore 发布规范检查工具对仅修改根目录 `README.md` 的纯文档 PR 错误触发了路径格式校验，报告 `[Path Error] The expected path should be /README.md`。

## 修改的文件
无（基础设施问题，非源码问题）

## 修复逻辑
该 PR (#2790) 仅修改了根目录 `README.md`（更新镜像 Tags 列表），属于纯文档变更，未涉及任何应用镜像目录、Dockerfile 或元数据文件。CI 的 appstore 发布规范检查工具（`eulerpublisher/update/container/app/update.py`）错误地将根目录 `README.md` 纳入校验范围，且因 `git diff --name-only` 输出的路径缺少前导 `/` 导致路径格式校验失败。

此问题根源在 CI 流水线层或 `eulerpublisher` 工具的过滤逻辑缺陷——对纯文档 PR 也触发了应用镜像发布规范检查。需要 CI 流水线维护人员修复触发条件或文件变更过滤逻辑（例如：当 PR 仅涉及根目录 `README.md` / `README.en.md` 等纯文档文件时，跳过 appstore 发布规范检查）。

本次 PR 的 `README.md` 内容本身没有问题，无需对源码进行任何修改。

## 潜在风险
无。未修改任何源代码。