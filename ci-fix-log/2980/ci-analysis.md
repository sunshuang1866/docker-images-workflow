# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, repo, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

此外，同一次 `dnf install` 中还有两个包也触发了相同的 HTTP/2 流错误，但重试后成功：
- `cmake-data-3.31.12-1.oe2403sp4.noarch.rpm`（1199s）
- `git-core-2.54.0-2.oe2403sp4.x86_64.rpm`（1776s）

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件源镜像在通过 HTTP/2 协议下发 RPM 包时频繁触发 `INTERNAL_ERROR`（Curl error 92），导致特定包（`gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm`，约 13MB）经过多次重试仍下载失败，`dnf install` 整体报错退出。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了一个语法正确、依赖声明合理的 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）。失败纯粹由 openEuler 24.03-LTS-SP4 软件源镜像的 HTTP/2 服务端稳定性问题导致，属于 CI 基础设施层面的瞬时故障。PR 中任何代码变更均未引入此问题，且该问题不会因修改 Dockerfile 内容而消失。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，Code Fixer 无需处理 Dockerfile。建议触发 CI 重试（re-run the failed job）。同一轮构建中 `cmake-data` 和 `git-core` 两个包也遭遇了相同的 HTTP/2 流错误但最终重试成功，说明该镜像源并非完全不可用，而是间歇性不稳定。`gcc-c++` 下载失败属于概率性事件，重新运行 CI 有较高概率通过。

### 方向 2（置信度: 低）
若多次重试均失败，需联系 openEuler 24.03-LTS-SP4 软件源运维团队排查 HTTP/2 服务端配置——从日志看错误类型为 `INTERNAL_ERROR (err 2)`，这是服务端主动发送的 RST_STREAM 帧，通常意味着服务端 HTTP/2 实现存在缺陷或后端存储/代理存在间歇性错误。

## 需要进一步确认的点
- 若该 PR 在其他架构（如 arm64/aarch64）的 CI job 中也失败，可交叉验证是否为同一软件源镜像问题，还是仅限 x86_64 节点/镜像。
- 若多次重试 `gcc-c++` 包下载均失败，需确认该特定 RPM 文件在镜像源上是否完整（文件大小、SHA256 校验），排除文件损坏的可能。

## 修复验证要求
无需验证。此失败为 infra-error，不涉及代码变更。
