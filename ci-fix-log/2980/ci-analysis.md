# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, MIRROR, No more mirrors to try

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
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 连接出现多次流错误（`INTERNAL_ERROR (err 2)`），导致 `gcc-c++` 等多个 RPM 包下载失败。`gcc-c++` 包在两次 HTTP/2 流错误后耗尽了所有 mirror 重试，最终 `dnf install` 报错退出。

### 与 PR 变更的关联
**与 PR 的代码改动无关。** 这是一个纯粹的 CI 基础设施问题——openEuler 24.03-LTS-SP4 的软件仓库（`repo.****.org`）在 Docker 构建期间的 HTTP/2 传输不稳定，导致大文件（如 `gcc-c++` 约 13MB、`gcc` 约 34MB、`cmake-data` 约 2.1MB、`git-core` 约 11MB）下载过程中 HTTP/2 帧层出现内部错误。PR 中新增的 Dockerfile 自身语法正确、包名列表有效，且部分包（`acl`、`automake`、`gcc` 等）已成功下载，仅部分包触发了网络层面的传输错误。

## 修复方向

### 方向 1（置信度: 中）
这是一个临时性的仓库网络问题。最简单的处理方式是**重试 CI 构建**——openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 流错误可能已自行恢复。如果仓库稳定性持续存在问题，可考虑在 `dnf install` 前设置 `http2=false` 强制使用 HTTP/1.1 规避 HTTP/2 帧层错误：
```dockerfile
RUN echo "http2=false" >> /etc/yum.repos.d/*.repo && dnf install -y ...
```
但不推荐将此类网络规避措施固化到 Dockerfile 中，因为这属于基础设施层面的临时问题。

### 方向 2（置信度: 低）
如果重试后相同错误反复出现且仅针对 24.03-LTS-SP4 仓库，可能是该仓库的 HTTP/2 服务端实现存在缺陷，需要联系 openEuler 基础设施团队排查仓库服务端问题。

## 需要进一步确认的点
1. 重试 CI 构建是否能够通过。如果重试后成功，则确认是临时性网络抖动。
2. 同一时间段内其他使用 `openeuler:24.03-lts-sp4` 基础镜像的 PR 是否也遇到了相同的 `Curl error (92): Stream error in the HTTP/2 framing layer` 错误。如果多个 PR 同时受影响，则说明 openEuler 24.03-LTS-SP4 仓库确实存在 HTTP/2 服务端问题。
3. 该错误是否也在 aarch64 构建节点上出现（当前日志仅包含 x86_64 节点信息）。
