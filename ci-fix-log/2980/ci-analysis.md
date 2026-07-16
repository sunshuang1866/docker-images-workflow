# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install ...` 步骤）
- 失败原因: CI 构建环境在 `dnf install` 从 `repo.****.org`（openEuler 24.03-LTS-SP4 软件仓库）下载 RPM 包时，多个包（cmake-data、git-core、gcc-c++）遭遇 HTTP/2 协议层 Stream error（Curl error 92: `INTERNAL_ERROR`），dnf 在尝试所有镜像后均失败，导致 258 个包的整体下载事务失败。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了一个完整的 grads 2.2.3 Dockerfile（以及配套的 meta.yml、README.md、image-info.yml 条目），Dockerfile 内容正确、包名有效。错误发生在 `dnf install` 从远端仓库下载 RPM 包的网络传输阶段，属于 CI 基础设施与 openEuler 镜像站之间的网络/协议层问题，与 PR 代码改动无因果关联。

## 修复方向

### 方向 1（置信度: 中）
**等待并重试**：该错误为 HTTP/2 流异常导致的临时性网络故障（非代码或配置错误），最可能的原因是 openEuler 24.03-LTS-SP4 仓库镜像 `repo.****.org` 在构建时刻的 HTTP/2 服务不稳定。建议在 CI 中重新触发该 job（re-run），网络恢复后有望通过。

### 方向 2（置信度: 低）
**调整 dnf 配置禁用 HTTP/2**（仅当反复重试仍失败时考虑）：若仓库镜像持续存在 HTTP/2 协议兼容性问题（如反向代理/负载均衡器与 libcurl 的 HTTP/2 实现不兼容），可在 Dockerfile 的 `dnf install` 前添加 `RUN echo "http2=false" >> /etc/dnf/dnf.conf` 强制 dnf 降级使用 HTTP/1.1。

## 需要进一步确认的点
1. `repo.****.org` 的 openEuler 24.03-LTS-SP4 仓库镜像当前是否可正常访问并完整下载所列 RPM 包。
2. 该仓库镜像的 HTTP/2 实现是否存在与 BuildKit 容器环境内 libcurl 版本的已知兼容性问题。
3. 同一时段其他基于 `openeuler:24.03-lts-sp4` 的镜像构建是否也出现类似 failure，以判断是否为系统性网络故障。
