# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），非 PR 代码变更所致。

## 修改的文件
无

## 修复逻辑
CI 构建失败的直接原因是 openEuler 24.03-LTS-SP4 仓库镜像站在下载 RPM 包时出现 HTTP/2 流错误（`Curl error (92): Stream error in the HTTP/2 framing layer: INTERNAL_ERROR (err 2)`），导致 `gcc`、`gcc-gfortran`、`guile` 等多个包下载失败，最终 `dnf install` 以退出码 1 失败。

该失败：
- 发生在 Dockerfile 第 7-10 行的基础依赖安装阶段（`RUN dnf install -y ...`），尚未到达 PR 新增的任何业务逻辑
- 同为 24.03-LTS-SP4 源的运行时阶段 (#7) 也出现了相同的 HTTP/2 流错误
- 与 PR #2992 的代码变更完全无关，属于 openEuler 镜像服务器的临时性协议栈故障

**建议操作：重新触发 CI 构建。** 待镜像站 HTTP/2 服务恢复正常后，该镜像应能成功构建。

## 潜在风险
无。本次未对任何文件进行代码修改。