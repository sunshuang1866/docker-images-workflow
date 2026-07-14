# 修复摘要

## 修复的问题
无代码修复。本次 CI 失败为 infra-error（基础设施问题），由 `repo.openeuler.org` 仓库服务器的 HTTP/2 流协议瞬时故障导致，与 PR #2991 的代码变更无关。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 在 aarch64 runner 上执行 `dnf install` 时，`repo.openeuler.org` 仓库服务器多次出现 HTTP/2 流错误（`INTERNAL_ERROR (err 2)`），导致 `git-core`、`gcc-c++`、`guile` 三个 RPM 包下载失败。其中 `guile` 包在耗尽所有镜像重试后仍未成功，`dnf` 最终以 exit code 1 失败。PR 仅新增了标准格式的 Dockerfile，语法和逻辑正确，失败完全由仓库服务器端瞬时故障引起。

**建议操作**：对该 PR 的 CI 构建执行 rerun / rebuild，通常重试即可成功。若多次重试仍失败，需联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 服务端问题。

## 潜在风险
无