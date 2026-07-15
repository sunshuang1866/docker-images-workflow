# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 openEuler 24.03-LTS-SP4 软件包仓库服务器的 HTTP/2 协议层临时故障（Curl error 92: HTTP/2 stream INTERNAL_ERROR），属于 infra-error，与 PR #2992 的代码变更无关。

## 修改的文件
无。未修改任何文件。

## 修复逻辑
分析报告明确指出这是一个 infra-error：`dnf install` 在下载 `gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等 RPM 包时，openEuler 24.03-LTS-SP4 仓库服务器反复返回 HTTP/2 `INTERNAL_ERROR`，导致所有镜像重试耗尽后构建失败。PR 新增的 Dockerfile 内容和包名配置均正确，两份构建阶段（builder 和 stage-1）在下载不同包时均遭遇相同错误，佐证为仓库侧问题。在仓库服务恢复后重新触发 CI 构建即可。

## 潜在风险
无。