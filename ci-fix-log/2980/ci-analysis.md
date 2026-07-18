# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

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
- 失败原因: openEuler 24.03-LTS-SP4 的包仓库镜像站在 HTTP/2 协议层面不稳定，导致多个 RPM 包下载时出现 `Curl error (92): Stream error in the HTTP/2 framing layer`。其中 `cmake-data` 和 `git-core` 在重试后成功下载，但 `gcc-c++`（13MB）在两次不同 HTTP/2 stream 上均失败，最终所有镜像均耗尽，dnf 安装整体失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 Dockerfile 及配套的元数据/文档文件（README.md、image-info.yml、meta.yml），失败发生在 Docker 构建阶段 `dnf install` 从 openEuler 官方仓库下载编译依赖包时。该仓库镜像站的 HTTP/2 服务端稳定性问题是 CI 基础设施层面的问题，任何需要在本次构建中从该仓库下载大量包的 PR 都可能复现此失败。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。该失败为 openEuler 24.03-LTS-SP4 软件仓库镜像站的 HTTP/2 临时性不稳定导致，属于偶发性基础设施故障。重新触发 CI（如通过 `/retest` 或对 PR 提交空 amend commit）大概率能够通过。

### 方向 2（置信度: 低）
如果多次重试仍失败，可考虑在 `dnf install` 命令前添加重试/降级逻辑，例如关闭 HTTP/2（`echo "http2=false" >> /etc/dnf/dnf.conf`）强制使用 HTTP/1.1 进行包下载，规避 HTTP/2 stream 中断问题。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像站在当前时间的 HTTP/2 服务可用性（此问题是否为临时性的）
- 如果同仓库其他 PR（同样使用 `openeuler/openeuler:24.03-lts-sp4` 基础镜像且需要大体积 dnf 安装的）也出现类似 HTTP/2 stream error，则可确认是仓库端问题而非本 PR 特有问题
