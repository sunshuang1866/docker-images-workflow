# 修复摘要

## 修复的问题
无需代码修改。CI 失败根因是 openEuler 24.03-LTS-SP4 官方软件仓库在构建时出现 HTTP/2 流层协议异常（Curl error 92: INTERNAL_ERROR），属于基础设施临时故障，与 PR #2992 的 Dockerfile 内容无关。

## 修改的文件
无。PR 的 Dockerfile 语法和逻辑均正确，不需要任何代码修改。

## 修复逻辑
该失败类型为 `infra-error`，CI 构建环境从 `repo.****.org` 下载 RPM 包时遭遇 HTTP/2 流协议错误，多个包（gcc-gfortran、glibc-devel、guile、gcc）均受影响，dnf 尝试所有镜像后仍失败。这是软件源服务端的临时故障。修复方向：在仓库网络恢复后重新触发 CI 构建即可通过。

## 潜在风险
无。不涉及任何代码变更。