# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败原因: DNF 从 openEuler 24.03-LTS-SP4 软件仓库下载 RPM 包时，多个包（`cmake-data`、`git-core`、`gcc-c++`）遭遇 HTTP/2 流层错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），`gcc-c++` 在所有镜像源重试后均失败，导致整个 `dnf install` 命令以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 语法正确，`dnf install` 所列包名均存在于 openEuler 24.03-LTS-SP4 仓库中（依赖解析阶段已成功列出 258 个包和 914 MB 总下载量）。失败纯粹是因为 CI 构建环境与 openEuler 软件仓库之间的网络连接在 HTTP/2 层面不稳定，部分 RPM 包下载时流被服务端异常关闭。日志中另有部分包（如 `cmake`、`cpp`、`gcc` 等）下载成功，说明仓库地址正确、包名有效，问题出在网络传输层而非 Dockerfile 配置。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，等待基础设施恢复后重试。** 这是典型的 CI 基础设施网络问题（软件仓库 HTTP/2 流异常），与 PR 代码无关。建议在 CI 中重新触发本次构建，或在仓库网络状况稳定后重试。

### 方向 2（置信度: 低）
如反复重试仍失败，可在 Dockerfile 的 `dnf install` 命令前添加 `RUN echo "retries=10" >> /etc/dnf/dnf.conf && echo "timeout=120" >> /etc/dnf/dnf.conf` 增加 DNF 的重试次数和超时时间，提高对偶发网络波动的容忍度。但这仅能缓解症状，不能根治 HTTP/2 流错误。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 软件仓库镜像（`repo.****.org`）在 CI 构建时段是否存在服务端 HTTP/2 实现缺陷或负载过高的问题。
- 同一时段其他使用 openEuler 24.03-lts-sp4 基础镜像的 PR 是否也遇到相同错误（如果是，则确认为仓库端问题）。
