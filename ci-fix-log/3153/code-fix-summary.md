# 修复摘要

## 修复的问题
无需代码修改。CI 失败原因为 infra-error：CI appstore 发布规范预检工具 (`eulerpublisher/update/container/app/update.py`) 对根目录文档文件 (`README.md`, `README.en.md`) 进行了不合理的路径校验，这两个文件不属于任何应用镜像定义目录，不应受 appstore 校验约束。

## 修改的文件
无。

## 修复逻辑
本 PR 仅修改了仓库根目录下的纯文档文件 `README.md` 和 `README.en.md`（更新基础镜像 tags 链接），不涉及任何应用镜像 Dockerfile 或 `image-list.yml`。CI 的 appstore 校验工具将所有 PR 变更文件都纳入路径校验范围，未能豁免根目录非镜像文档，这是 CI 工具/流程侧的问题，需要在 `update.py` 中增加对根目录文档文件的豁免逻辑，或配置纯文档 PR 的跳过机制。PR 自身的文件变更内容没有问题，无需代码修改。

## 潜在风险
无。