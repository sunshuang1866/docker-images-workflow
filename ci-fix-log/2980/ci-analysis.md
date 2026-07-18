# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2传输中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, gcc-c++

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6` — `RUN dnf install -y` 步骤
- 失败原因: CI 构建节点在通过 dnf 从 openEuler 24.03-LTS-SP4 的 OS 仓库下载 RPM 包时，多个包（cmake-data、git-core、gcc-c++）遇到 HTTP/2 流传输错误（Curl error 92: INTERNAL_ERROR），cmake-data 和 git-core 经镜像重试后成功下载，但 gcc-c++（13 MB）在两次重试后仍失败，最终所有镜像耗尽，dnf 安装过程退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关**。PR #2980 仅新增了 grads 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中 `dnf install` 声明的所有包在 DNF 依赖解析阶段均已正确识别（258 个包全部解析成功），失败是 CI 构建环境与 openEuler RPM 镜像仓库之间的网络传输不稳定所致，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。本次失败为 CI 基础设施网络波动导致的 dnf 包下载瞬断，所有 RPM 包在仓库中均存在且可正确解析。无需修改任何代码或 Dockerfile，直接触发 CI 重新构建即可。若连续多次重试均以相同错误失败，则需排查 openEuler 24.03-LTS-SP4 的 OS 仓库镜像站状态或 CI 节点的网络配置。

## 需要进一步确认的点
- 检查 openEuler 24.03-LTS-SP4 OS 仓库镜像站（`repo.****.org`）在构建时段是否存在网络抖动或 HTTP/2 服务不稳定的情况。
- 确认 CI 构建节点到该仓库的网络链路是否正常（MTU、HTTP/2 兼容性等）。
- 若重试后仍然失败，需排查 dnf 配置中是否仅有该仓库的镜像，或该仓库是否已对某个较大包（如 gcc-c++ 13 MB）的 HTTP/2 传输存在已知问题。

## 修复验证要求
无。本次失败为 infra-error，与 PR 代码变更无关，Code Fixer 无需执行任何修改操作。
