# 修复摘要

## 修复的问题
无需代码修改。CI 失败是 **infra-error**（基础设施误报），非 PR 变更内容有问题。

## 修改的文件
无

## 修复逻辑
PR #3153 仅修改了仓库根目录的 `README.md`（更新基础镜像可用 tags 列表），修改内容完全正确。

CI 失败的直接原因是 `eulerpublisher/update/container/app/update.py` 的 appstore 发布规范预检工具检测到 `README.md` 发生变更，但该文件位于仓库根路径，不符合工具期望的镜像发布目录规范（如 `Category/Image/Version/OS/Dockerfile`），因此报 `Path Error`。

本质上是 CI 流水线无法区分"纯文档更新 PR"和"应包含镜像发布内容的 PR"，将合法的文档变更误判为路径错误。这是 CI 基础设施层面的问题，应在 Jenkins pipeline 中增加对仅 `.md` 文件变更的跳过逻辑，或修改 `update.py` 的路径校验/白名单机制。

由于 `README.md` 的修改内容正确无误，且该文件是 `pr.changed_files` 中唯一可修改的文件，不存在对源码的修改需求。

## 潜在风险
无（未修改任何代码）