# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`RUN dnf install -y` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 连接出现流错误（`INTERNAL_ERROR`），导致多个 RPM 包下载中断。`cmake-data` 和 `git-core` 在重试后成功下载，但 `gcc-c++` 两次尝试均失败，dnf 耗尽所有镜像重试后放弃。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了 GrADS 2.2.3 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及相关元数据文件。Dockerfile 中 `dnf install` 命令语法正确、包名无误，错误发生在从远端仓库下载 RPM 包的网络传输阶段，属于 CI 基础设施/外部仓库服务的瞬时问题。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。该错误属于外部仓库服务的瞬时网络故障（HTTP/2 流被服务端以 INTERNAL_ERROR 异常关闭）。在同一 CI 构建中，`cmake-data` 和 `git-core` 首次遇到同样的错误后重试成功，仅 `gcc-c++` 始终失败。最可能的根因是 openEuler 24.03-LTS-SP4 仓库在该时间段内服务不稳定。建议等待仓库服务恢复后重新触发 CI，大概率可自然通过。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在构建时间段是否有服务异常/维护记录
- 如果重试仍然失败，需排查是否仓库对特定 IP 段或 CI runner 的 HTTP/2 连接存在限制策略
- 可尝试在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制禁用 HTTP/2，改用 HTTP/1.1 降低流层协议问题的影响
