# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, No more mirrors to try

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

#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库镜像（`repo.****.org`）在 x86_64 构建节点上出现 HTTP/2 流传输错误，导致 `gcc-c++` 包的两次下载均失败（cmake-data 和 git-core 经重试后成功，gcc-c++ 两次均失败），DNF 耗尽所有镜像后放弃安装。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准格式的 Dockerfile（含 `dnf install` 构建依赖步骤，与同项目其他 Dockerfile 模式一致）和元数据文件。失败是由 openEuler 24.03-LTS-SP4 软件仓库镜像在构建时刻的网络/服务端 HTTP/2 不稳定导致，属于 CI 基础设施问题，Dockerfile 本身无任何错误。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试构建即可。** 这是 openEuler 24.03-LTS-SP4 仓库镜像的临时性 HTTP/2 服务端故障（`Curl error (92)`），与 PR 新增的 Dockerfile 无关。等待仓库镜像恢复后重新触发 CI 构建，大概率能直接通过。

### 方向 2（置信度: 低）
如果仓库镜像持续不稳定，可在 `dnf install` 前添加 `dnf config-manager --setopt=max_parallel_downloads=1` 或降级为 HTTP/1.1（`echo "http2=false" >> /etc/dnf/dnf.conf`），减少 HTTP/2 多路复用带来的 stream error 风险。但这是绕过措施而非根因修复，优先建议方向 1。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）当前是否已恢复正常。可通过在另一台 x86_64 机器上执行 `dnf download --url gcc-c++` 验证仓库可达性。
- 如果多次重试均失败，需要联系 openEuler 基础设施团队排查仓库 HTTP/2 服务端问题。
