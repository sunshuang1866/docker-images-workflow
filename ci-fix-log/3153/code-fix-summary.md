# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error：appstore 发布规范校验工具对仅包含文档变更的 PR 错误触发了路径校验。

## 修改的文件
无

## 修复逻辑
该 PR (#3153) 仅修改了 `README.md` 和 `README.en.md` 两个根目录级项目文档文件，更新了可用基础镜像标签列表。CI 管道的 appstore 发布规范校验工具 (`eulerpublisher/update/container/app/update.py`) 将这两个 README 文件视为 appstore 镜像提交进行路径合规检查，因其不在 `AI/`、`Bigdata/`、`Cloud/` 等应用镜像场景目录下而报路径错误。

这是 CI 基础设施（校验工具）的误报，与 PR 变更无因果关系。校验工具应在检测到变更文件仅包含非 appstore 路径的文件时自动跳过该校验，或通过 PR 标签/commit message 触发跳过。修复应在 CI 流水线侧进行，而非修改源文件。

## 潜在风险
无