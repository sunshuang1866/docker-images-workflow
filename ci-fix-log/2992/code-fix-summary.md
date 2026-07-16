# 修复摘要

## 修复的问题
无需代码修改。该 CI 失败为 openEuler 24.03-LTS-SP4 官方 RPM 仓库的 transient HTTP/2 协议层故障（Curl error 92: Stream error in the HTTP/2 framing layer），属于 CI 基础设施问题（infra-error），与 PR 变更无关。

## 修改的文件
无。所有 PR 涉及的文件（Dockerfile、README.md、image-info.yml、meta.yml）无需修改。

## 修复逻辑
分析报告明确判定该失败为 infra-error，根因是 openEuler 24.03-LTS-SP4 仓库服务器侧的 HTTP/2 协议层间歇性错误，导致 `dnf install` 下载 RPM 包时多个包（gcc-gfortran、glibc-devel、guile、gcc）下载失败。该问题与 Dockerfile 内容和 PR 新增的 SP4 支持无关——Dockerfile 结构与已有的 SP3 版本完全一致。

修复方向：重新触发 CI 构建即可。此类 HTTP/2 Stream INTERNAL_ERROR 通常是服务器端或中间代理/LB 的间歇性问题，短时间内重试大概率会成功。

若多次重试仍持续失败，需联系 openEuler 仓库运维排查 SP4 仓库 HTTP/2 服务状态，或在 Dockerfile 中将 dnf repo 显式指定为备选镜像站（如 `repo.huaweicloud.com`）。

## 潜在风险
无。