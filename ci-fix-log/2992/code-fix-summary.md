# 修复摘要

## 修复的问题
无需代码修改 — 失败为 openEuler 24.03-LTS-SP4 仓库镜像的临时性 HTTP/2 传输层故障（infra-error）。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`，置信度为高。根因是 openEuler 24.03-LTS-SP4 仓库镜像在 CI 构建期间出现 Curl error (92): Stream error in the HTTP/2 framing layer，导致大型 RPM 包（gcc、gcc-gfortran、guile）下载时 HTTP/2 stream 被非正常关闭（INTERNAL_ERROR），dnf 重试耗尽所有镜像后安装失败。

PR #2992 的新增 Dockerfile 内容与已有的 sp3 版本 Dockerfile 结构一致，仅基础镜像从 `24.03-lts-sp3` 改为 `24.03-lts-sp4`，PR 变更与此次失败无因果关系。此类网络故障通常在镜像站恢复后重试 CI 即可通过。

## 潜在风险
无