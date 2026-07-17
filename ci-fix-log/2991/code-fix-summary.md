# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 `repo.openeuler.org` 的 HTTP/2 CDN 基础设施故障，与 PR #2991 新增的 Dockerfile 变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确判定失败类型为 **infra-error**。aarch64 runner 在构建时，`repo.openeuler.org` 的 HTTP/2 服务端对多个 RPM 包（`git-core`、`gcc-c++`、`guile`）均返回 `Curl error (92): Stream error in the HTTP/2 framing layer`，其中 `guile` 重试所有镜像后仍失败，导致 `dnf install` 整体退出。`git-core` 和 `gcc-c++` 也遭遇了同样的 HTTP/2 流错误（仅因重试才成功），进一步佐证这是仓库服务端问题。PR 新增的 `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 是项目中大量 Dockerfile 共用的通用依赖安装模式，代码本身无缺陷。

应重新触发 CI（re-trigger），在网络恢复后构建预期可通过。若问题持续，可考虑在 Dockerfile 中配置 dnf 禁用 HTTP/2（`http2=false`）或添加备用镜像源，但这属于对基础设施问题的规避措施，非本次 PR 代码修复范围。

## 潜在风险
无