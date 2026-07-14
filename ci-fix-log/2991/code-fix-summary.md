# 修复摘要

## 修复的问题
无需代码修复。CI 失败由 `repo.openeuler.org` 仓库服务器的 HTTP/2 流协议瞬时故障（Curl error 92: INTERNAL_ERROR (err 2)）导致 `dnf install` 下载 RPM 包失败，属于 CI 基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
分析报告确认：
- 失败位置：`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6` 的 `dnf install` 命令
- 失败原因：`repo.openeuler.org` 服务器在 aarch64 runner 上出现 HTTP/2 流协议错误，导致 `git-core`、`gcc-c++`、`guile` 三个 RPM 包下载失败
- 与 PR 的关联：无关。PR 仅新增了一个标准格式的 Dockerfile，Dockerfile 本身语法和逻辑正确

建议对 PR 触发 rerun/rebuild，重试通常即可成功。

## 潜在风险
无