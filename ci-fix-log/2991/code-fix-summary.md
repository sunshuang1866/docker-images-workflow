# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施故障（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败原因是 `repo.openeuler.org` 镜像站在 aarch64 构建节点上发生 HTTP/2 协议层流错误（Curl error 92: `Stream error in the HTTP/2 framing layer`），导致 `dnf install` 下载 RPM 包时部分包（`git-core`、`gcc-c++`、`guile`）下载失败。这是 openEuler 官方仓库服务器的瞬时性 HTTP/2 传输层问题，属于基础设施故障。

PR 仅新增了标准的 vvenc 1.14.0 Dockerfile（安装构建工具后编译 vvenc）及元数据文件，Dockerfile 中的 `dnf install` 包列表完全正确，均为 openEuler 系统仓库的合法包名。所有 PR 文件无需修改。

**建议操作**：触发 CI 重新构建。若多次重试仍失败，可考虑在 Dockerfile 中 `dnf install` 前添加 HTTP/1.1 降级配置或换用其他镜像源。

## 潜在风险
无