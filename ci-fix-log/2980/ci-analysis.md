# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境中 `repo.****.org`（openEuler 24.03-LTS-SP4 官方 RPM 镜像仓库）出现 HTTP/2 协议层错误（Curl error 92: Stream error in the HTTP/2 framing layer），导致多个 RPM 包（cmake-data、git-core、gcc-c++）下载失败。其中 `git-core` 重试后成功下载，但 `gcc-c++` 的两次重试均以相同的 HTTP/2 流错误失败，所有可用镜像均已尝试，`dnf` 最终报错退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅为新增 grADS 镜像在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套的 README、image-info.yml、meta.yml 更新。Dockerfile 中的 `dnf install` 命令语法正确，所列包名均为 openEuler 24.03 仓库中的有效包（从日志中可见 Dependencies resolved 阶段列出了全部 258 个待安装包及其正确仓库来源）。失败纯粹是由于 CI 基础设施中 `repo.****.org` RPM 镜像仓库的 HTTP/2 协议层瞬时故障导致的包下载失败，与 PR 代码内容无关。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 这是一个镜像仓库瞬时网络故障，与 PR 代码变更无关。在 `repo.****.org` 镜像仓库恢复正常后重新触发 CI 构建即可通过。无需修改任何代码。

### 方向 2（置信度: 低，仅在问题持续出现时考虑）
若重试后仍持续出现相同错误，可考虑在 Dockerfile 的 `dnf install` 前添加重试逻辑（如 `dnf install -y --setopt=retries=10 ...`），或降级 DNF 的 HTTP 后端为 HTTP/1.1（`echo "http2=false" >> /etc/dnf/dnf.conf`），以规避 HTTP/2 协议的瞬时错误。但这不是推荐的修复方案，优先应确认镜像仓库端的问题是否已修复。

## 需要进一步确认的点
1. 确认 `repo.****.org` 镜像仓库当前状态是否正常（是否正在进行维护或存在已知的 HTTP/2 代理层故障）。
2. 确认在其他 openEuler 24.03-lts-sp4 镜像的近期构建中是否也出现了相同的 HTTP/2 流错误，以判断影响范围（是 `repo.****.org` 的瞬时故障还是对特定 IP/子网的访问量限制）。
