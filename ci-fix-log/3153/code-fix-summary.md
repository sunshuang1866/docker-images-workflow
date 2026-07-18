# 修复摘要

## 修复的问题
无需代码修改。此 CI 失败为基础设施误报——`eulerpublisher` 工具的 appstore 发布预检将根级 `README.md` 的纯文档变更误判为需要参与应用镜像发布路径校验，导致 "Path Error"。

## 修改的文件
无。

## 修复逻辑
PR #3153 是一个纯文档更新（`docs: update available base image tags in README`），仅修改了仓库根级的 `README.md` 和 `README.en.md`，用于更新基础镜像的可用 tags 列表。这些文件的变更属于正常的仓库维护工作，不应受 appstore 发布路径规范约束。

CI 失败根因在于 `eulerpublisher` 工具的 appstore 预检环节未区分"纯文档 PR"和"镜像发布 PR"，对所有 PR 的文件变更统一进行 appstore 路径校验，而根级 `README.md` 不符合 `{分类}/{镜像名}/{版本}/{OS版本}/` 的发布路径模式，导致检查报错。这不是 `README.md` 文件本身的问题，而是 CI 流程设计上的限制。

**修复应在 CI 流水线配置层面进行**，而非修改 PR 文件：需在 Jenkinsfile 或等效 CI 配置中增加对根级文档文件（如 `/README.md`、`/README.en.md`）的 appstore 检查豁免逻辑，使纯文档 PR 不被纳入 appstore 路径校验。

## 潜在风险
无——未修改任何代码文件。若强行修改 `README.md` 以绕过 CI 检查（如添加伪造的路径结构注释），将破坏文档可读性，属于不正确的修复方式。