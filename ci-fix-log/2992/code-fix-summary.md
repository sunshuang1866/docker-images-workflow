# 修复摘要

## 修复的问题
CI 失败为 `infra-error`，由 openEuler 24.03-LTS-SP4 软件包仓库 HTTP/2 服务端不稳定导致，无需代码修改。

## 修改的文件
无。该失败属于基础设施问题，PR 变更的 Dockerfile 和其他文件不存在语法或逻辑错误，无需修改任何代码。

## 修复逻辑
构建日志中多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载时遭遇 Curl error (92): Stream error in the HTTP/2 framing layer (INTERNAL_ERROR)，且 `gcc` 包在所有镜像站重试后仍无法下载。同时构建的 stage-1 阶段也出现相同 HTTP/2 流错误，证实问题出在仓库服务器端而非 Dockerfile 配置。PR 仅新增了 multiwfn 的 openEuler 24.03-LTS-SP4 版本 Dockerfile 及配套文档条目，`dnf install` 命令格式和包名与已有的 sp3 版本一致。建议重新触发 CI 构建（retry/rerun），待仓库服务恢复正常后构建应能通过。

## 潜在风险
无。不进行任何代码修改，不会引入新风险。