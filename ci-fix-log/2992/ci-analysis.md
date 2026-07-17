# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf, MIRROR

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像（`repo.****.org`）在 HTTP/2 传输层发生间歇性流错误（Curl error 92: INTERNAL_ERROR），导致多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载失败。dnf 重试所有镜像后仍无法完成下载，构建终止。

### 与 PR 变更的关联
**与 PR 无关。** 此次 PR 仅新增了 Multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件。Dockerfile 中的 `dnf install` 命令语法正确、包名有效。失败完全由 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 传输层问题导致，属于 CI 基础设施层面的故障。两个构建阶段（builder 的 #8 和 stage-1 的 #7）均受到同样的 HTTP/2 流错误影响，进一步排除了 Dockerfile 配置问题。

## 修复方向

### 方向 1（置信度: 中）
等待 openEuler 24.03-LTS-SP4 仓库镜像恢复后重新触发 CI 构建。此问题为服务端 HTTP/2 实现缺陷或网络中间设备干扰导致的间歇性连接异常，与 PR 代码变更无关，重试即可。若持续失败，需联系 openEuler 基础设施团队排查仓库 CDN/代理的 HTTP/2 配置。

### 方向 2（置信度: 低）
若仓库 HTTP/2 问题长期无法解决，可在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或 `echo "max_parallel_downloads=1" >> /etc/dnf/dnf.conf` 来降低下载并发度和禁用 HTTP/2，以规避服务端 HTTP/2 流错误。但此方向仅为规避手段，不应作为正式修复方案。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）的 HTTP/2 服务是否稳定——该错误是否为已知的临时性问题，还是该仓库对某些网络环境持续不稳定。
- 同一时间段内其他使用 `openeuler:24.03-lts-sp4` 基础镜像的 PR 是否也遇到相同错误（可交叉验证是否为系统性仓库故障）。
- CI 构建节点的网络环境是否通过了可能干扰 HTTP/2 长连接的中间代理或负载均衡器。
- 日志中 `repo.****.org` 的具体域名需要确认，以判断是否有可替代的镜像源。
