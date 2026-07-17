# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），与 PR 代码变更无直接关联。

## 修改的文件
无（infra-error，不修改任何代码文件）

## 修复逻辑
CI 失败的原因是 openEuler 24.03-LTS-SP4 仓库镜像服务器在处理 HTTP/2 流时频繁返回 `INTERNAL_ERROR`（Curl error 92），导致多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载失败。该错误属于仓库服务器端的临时性协议问题，而非 PR 新增的 Dockerfile 代码错误。

PR #2992 仅新增了一个标准的多阶段构建 Dockerfile，语法和包名均无错误。同一构建任务中其他使用 SP3 仓库的 dnf 命令正常运行，进一步证明问题出在远端仓库服务而非 PR 代码。

**建议操作**：重试 CI 任务。若多次重试均失败，需联系 openEuler 仓库运维团队排查 SP4 镜像源 HTTP/2 服务端问题。

## 潜在风险
无