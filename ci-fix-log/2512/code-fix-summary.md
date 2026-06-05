# 修复摘要

## 修复的问题
修复 Dockerfile 中浅克隆（`--depth 1`）与 `git checkout` 指定 commit hash 不兼容的构建逻辑缺陷。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 在第 23-24 行，将 `git checkout ${VERSION} 2>/dev/null || true` 替换为 `git fetch origin ${VERSION}` + `git checkout ${VERSION}`（移除错误静默掩盖）。

## 修复逻辑
分析报告指出：`git clone --depth 1` 浅克隆仅包含默认分支最新提交，不包含 `22fca04` 这个 commit 的完整历史。原代码中 `git checkout ${VERSION} 2>/dev/null || true` 在 checkout 失败时静默忽略错误，导致仓库实际停留在默认分支最新代码而非指定版本，最终引发 cmake 编译版本不匹配。

修复方案：在 checkout 前增加 `git fetch origin ${VERSION}` 来获取目标 commit 所需的必要历史，使 checkout 能正确定位到指定版本。同时移除原来的 `2>/dev/null || true` 错误掩盖，让 checkout 失败时能正确暴露问题。

## 潜在风险
- `git fetch origin ${VERSION}` 需要网络访问 github.com，在离线 CI 环境中可能失败。但这是纠正版本获取正确性的必要步骤，且失败会正确报错而非静默掩盖。
- 其他网络依赖（yum install、curl 安装 Rust）未配置重试机制，但分析报告证据不足，未作修改。如构建日志确认是网络问题，需后续跟进。