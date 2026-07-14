# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 **infra-error**：`repo.openeuler.org` 的 `openEuler-24.03-LTS-SP4` aarch64 仓库在 HTTP/2 传输层出现流错误（Curl error 92: `INTERNAL_ERROR`），导致 `dnf install` 下载 RPM 包失败。

## 修改的文件
无

## 修复逻辑
失败根因是 `repo.openeuler.org` 仓库服务端的 HTTP/2 协议异常，与 PR #2991 新增的 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6` 的 `dnf install` 命令）代码变更完全无关。Dockerfile 中 `dnf install -y git gcc gcc-c++ make cmake` 命令本身语法正确、依赖合理。

根据 CI 分析报告建议（方向 1，置信度: 高），该失败属于 CI 基础设施层面问题，应通过以下方式解决：
- 重试 CI 构建（若仓库端问题已修复）
- 或在 CI 编排侧配置 dnf/yum 回退到 HTTP/1.1
- 或更换 openEuler 镜像源

以上修复均属于 CI 编排/基础设施层面的调整，不在 PR 代码范围内。

## 潜在风险
无