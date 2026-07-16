# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2传输错误
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
- 失败原因: CI 构建环境从 openEuler 24.03-LTS-SP4 软件仓库镜像站下载 RPM 包时，HTTP/2 传输层发生流错误（`Curl error (92): INTERNAL_ERROR`），多个包（cmake-data、git-core、gcc-c++）均受波及。dnf 的重试机制成功恢复了 cmake-data 和 git-core 的下载，但 gcc-c++（13 MB）两次重试均失败，最终耗尽所有镜像重试次数，导致 `dnf install` 步骤整体失败。

### 与 PR 变更的关联
**与 PR 无直接关联。** PR 的代码变更仅为新增一个合法的 Dockerfile（包含 `dnf install` 构建依赖的标准步骤）以及配套的 README/meta/image-info 元数据更新。日志显示 dnf 的依赖解析阶段已成功完成（`#7 724.4 Dependencies resolved.`），列出了全部 258 个待安装包，说明 Dockerfile 中声明的包名均有效且存在于仓库中。失败发生在下载阶段，是由 openEuler 24.03-LTS-SP4 软件仓库镜像服务器的 HTTP/2 传输层不稳定导致的，属于基础设施层面问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 该错误为 openEuler 24.03-LTS-SP4 仓库镜像服务器的瞬时性 HTTP/2 传输故障。观察日志中 cmake-data 和 git-core 均在首次出错后通过 dnf 自动重试成功下载，仅 gcc-c++ 因两次重试均失败而最终失败。在镜像服务器恢复稳定后，重新触发 CI 构建有较大概率直接通过，无需修改任何代码。

### 方向 2（置信度: 中）
**联系基础设施团队检查镜像站健康状态。** 如果多次重试均在同一仓库镜像上失败，需确认 `repo.****.org` 的 openEuler-24.03-LTS-SP4 仓库镜像是否因负载、证书或 HTTP/2 配置问题导致客户端 curl 流传输错误。考虑更换备用镜像源或降级使用 HTTP/1.1 协议（在 `dnf.conf` 中禁用 HTTP/2）。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的官方仓库镜像站 `repo.****.org` 当前是否有已知的服务中断或性能降级公告。
- 确认该失败是否在 aarch64 等其他架构的构建 job 中同样出现（本次提供的日志仅为 x86-64 架构的构建日志）。
- 如果多次重试仍失败，确认是否有其他 openEuler 24.03-lts-sp4 镜像（如基础镜像 `openeuler/openeuler:24.03-lts-sp4` 的拉取及后续 `dnf install`）在同一时间段内也遭遇了类似问题，以确认是否为仓库侧的普遍性问题。
