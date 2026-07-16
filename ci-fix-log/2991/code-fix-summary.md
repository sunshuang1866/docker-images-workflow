# 修复摘要

## 修复的问题
CI 基础设施错误：openEuler 官方镜像站 `repo.openeuler.org` 在通过 HTTP/2 传输 aarch64 RPM 包时频繁出现流异常关闭（Curl error 92: Stream error in the HTTP/2 framing layer），导致 `dnf install` 下载失败。

## 修改的文件
无。该失败与 PR 代码变更无关，属于 CI 基础设施/上游镜像站的瞬时性问题。

## 修复逻辑
- 失败原因：openEuler 24.03-LTS-SP4 aarch64 仓库的 HTTP/2 服务端在传输特定 RPM 包时出现 INTERNAL_ERROR，导致 `git-core`、`gcc-c++`、`guile` 等包下载失败。
- 失败类型：`infra-error`（CI 基础设施问题），与 PR 中新增的 Dockerfile `RUN dnf install -y git gcc gcc-c++ make cmake` 命令无关。
- 推荐操作：重新触发 CI 构建重试，该问题为镜像站 HTTP/2 服务的瞬时性波动，多数情况下重试即可成功。
- 备选方案：若问题持续，可在 Dockerfile 第 6 行的 `dnf install` 命令中追加 `--setopt=retries=10` 提高网络容忍度（当前日志中 dnf 已自动重试但耗尽了所有镜像）。

## 潜在风险
无。未修改任何代码。