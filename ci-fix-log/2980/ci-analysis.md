# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP2流中断导致包下载失败
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, gcc-c++

## 根因分析

### 直接错误
```
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
------

ERROR: failed to solve: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库服务器在 HTTP/2 传输层频繁出现流中断（`INTERNAL_ERROR (err 2)`）。`gcc-c++` RPM 包经两次重试均失败后，dnf 所有镜像源均已用尽，包下载彻底失败。日志中同一构建进程内还有 `cmake-data`（#7 1199.1）和 `git-core`（#7 1776.2）的同类 HTTP/2 流错误，但均在后继重试中恢复，说明仓库 HTTP/2 实现在该时段处于极不稳定状态。

### 与 PR 变更的关联
**无关。** PR 变更内容仅为新增 GrADS 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及对应的 README、image-info.yml、meta.yml 元数据更新。Dockerfile 中 `dnf install` 的包列表语法正确，所有包名均为 openEuler 24.03-LTS-SP4 仓库中真实存在的包（日志中 dnf 解析出 258 个待安装包，包列表完整）。失败原因完全来自上游 openEuler 软件仓库的 HTTP/2 协议层故障，与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 低）
**重试即可**。这是仓库服务器端的瞬时网络故障，代码层面无需任何修改。等待仓库服务恢复后重新触发 CI 构建即可通过。

### 方向 2（置信度: 低）
如果仓库 HTTP/2 流中断问题持续复现，可尝试在 Dockerfile 的 `dnf install` 命令前添加 dnf 重试配置（如 `echo "retries=10" >> /etc/dnf/dnf.conf`），但该方案仅能缓解瞬时抖动，无法根治服务器端 HTTP/2 实现缺陷。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在构建时段是否存在已知的服务端 HTTP/2 协议问题或 CDN 节点故障。
2. 重新触发 CI 构建是否能通过——如果多次重试均在同一仓库同一包上失败，则可能是仓库侧存在持久性问题需向 openEuler 基础设施团队报告。
3. CI 构建环境中是否可配置 dnf 回退到 HTTP/1.1（如通过 `ip_resolve` 或 curl 全局配置禁用 HTTP/2），作为规避服务器端 HTTP/2 缺陷的备选方案。
