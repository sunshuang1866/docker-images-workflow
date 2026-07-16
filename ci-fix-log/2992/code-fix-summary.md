# 修复摘要

## 修复的问题
无需代码修复。此次 CI 失败为基础设施错误（infra-error），系 openEuler 24.03-LTS-SP4 镜像站 HTTP/2 连接不稳定导致包下载失败（Curl error 92: Stream error in the HTTP/2 framing layer），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 构建在 `dnf install` 阶段下载 RPM 包（gcc、gcc-gfortran、glibc-devel、guile 等）时，openEuler 镜像站返回 HTTP/2 流错误，dnf 重试所有镜像后放弃，导致构建失败。PR 仅新增了 Multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件，Dockerfile 语法和构建逻辑均正确。此问题为临时性网络/CDN 故障，建议重新触发 CI 构建。

## 潜在风险
无