# 修复摘要

## 修复的问题
无代码修改。CI 失败为 `infra-error`：CI 流水线的 `eulerpublisher` appstore 发布校验工具对纯文档变更 PR（仅修改 `README.md` 中的镜像 Tags 列表）错误地执行了镜像发布路径规范校验，属于 CI 基础设施误判，与 PR 改动内容无关。

## 修改的文件
无（无需修改源代码）

## 修复逻辑
该 PR 仅更新了 `README.md` 中可用镜像的 Tags 列表链接（如更新 24.03-lts-sp2 → 24.03-lts-sp3、新增 25.09 条目），属于纯文档维护变更，不涉及任何镜像的构建、发布或目录结构调整。CI 流水线中的 appstore 发布预检环节未能识别此 PR 为文档专用变更，错误地对根目录 `README.md` 执行了发布路径校验。修复应在 CI 编排层（Jenkins job 或 trigger 脚本）实现：在运行 `eulerpublisher` 检查前增加变更文件类型判断，若 PR 仅包含根目录文档文件且无镜像目录下 Dockerfile/meta.yml 等文件变更，则跳过该校验步骤。

## 潜在风险
无（未修改任何代码）