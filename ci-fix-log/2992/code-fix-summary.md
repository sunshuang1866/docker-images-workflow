# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：openEuler 24.03-LTS-SP4 软件源镜像在构建时出现 HTTP/2 流错误（Curl error 92），导致 `gcc` 等大型 RPM 包下载失败，耗尽所有镜像后 `dnf install` 中断。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认：失败类型为 `infra-error`，与 PR #2992 的代码变更无关。Dockerfile 中的 `dnf install` 命令语法正确、包名有效。多个 RPM 包（gcc、gcc-gfortran、guile、glibc-devel）均出现相同 HTTP/2 流错误，且 stage-1 中相同错误通过 dnf 自动重试成功，说明是间歇性网络服务端问题。修复方向为等待镜像站恢复后重新触发 CI 流水线。

## 潜在风险
无