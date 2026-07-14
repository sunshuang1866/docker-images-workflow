# 修复摘要

## 修复的问题
无需代码修改 — 该 CI 失败为 openEuler 官方镜像站 `repo.openeuler.org` 的 HTTP/2 服务端瞬时网络故障（infra-error），与 PR 代码无关。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 构建在执行 `dnf install` 下载 `guile` 包时，`repo.openeuler.org` 的 HTTP/2 连接反复报 `Curl error (92): Stream error in the HTTP/2 framing layer ... INTERNAL_ERROR`，`guile` 耗尽所有镜像重试后下载失败，导致 dnf 事务中断。

Dockerfile 第 6 行的 `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 命令语法和所请求的包均完全正确，问题在于构建时段 openEuler 镜像站对 aarch64 节点的 HTTP/2 服务不稳定。同一命令在其他构建任务中可正常执行。

**建议：在 CI 中重新触发该 job 的构建。** 如果连续多次重试仍失败，需联系 openEuler 镜像站运维排查 `guile` 包在 `openEuler-24.03-LTS-SP4/OS/aarch64/` 下的存储完整性。

## 潜在风险
无