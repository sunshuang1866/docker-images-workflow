# 修复摘要

## 修复的问题
无代码修复。CI 失败为 openEuler 24.03-LTS-SP4 仓库镜像 HTTP/2 协议层故障导致的临时性基础设施问题（infra-error），与 PR #2992 的代码变更无关。

## 修改的文件
无。本次失败属于 infra-error，无需修改任何源代码文件。

## 修复逻辑
CI 构建日志显示多个 RPM 包（gcc、gcc-gfortran、glibc-devel、guile）从 `repo.****.org` 下载时出现 Curl error (92): Stream error in the HTTP/2 framing layer: INTERNAL_ERROR。两个并行构建阶段（#7 和 #8）均遭遇同一仓库的 HTTP/2 流错误，证实问题出在仓库端而非 Dockerfile 配置。Dockerfile 的 `dnf install` 命令语法和包名均正确，与已有的 sp3 版本 Dockerfile 模式一致。

## 修复方向
等待 CI 基础设施恢复后重新触发构建。若多次重试后仍然失败，可在 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 临时禁用 HTTP/2 作为规避手段。

## 潜在风险
无