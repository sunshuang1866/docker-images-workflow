# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 包仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 705.6 Dependencies resolved.
#8 705.7 Total download size: 261 M
#8 705.7 Downloading Packages:
...
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
...
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
...
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
ERROR: failed to solve: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`
- 失败原因: CI 构建环境在执行 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，仓库服务器的 HTTP/2 连接多次出现流帧错误（Curl error 92: INTERNAL_ERROR），多个包（gcc-gfortran、glibc-devel、guile、gcc）下载失败，最终 gcc 包的所有镜像尝试均耗尽，dnf 安装失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅添加了 Multiwfn 在 openEuler 24.03-LTS-SP4 的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 语法正确，`dnf install` 命令格式无误。失败原因是 openEuler 24.03-LTS-SP4 包仓库的 HTTP/2 服务端在构建时段不稳定，导致 RPM 包下载阶段出现流协议错误。此为 CI 基础设施的临时性网络/服务端问题。

## 修复方向

### 方向 1（置信度: 高）
**建议直接重试 CI**。该失败为 transient infra-error，openEuler 24.03-LTS-SP4 包仓库在本次构建时段出现 HTTP/2 服务端流错误，属于临时性基础设施波动。多次 Curl error (92) 模式（stream 未被正确关闭）指向服务端 HTTP/2 实现问题或 CDN/代理层问题，非客户端配置或代码缺陷。重新触发 CI 构建即可，大多数情况下同一问题不会复现。

## 需要进一步确认的点
1. 若重试后仍反复出现相同 HTTP/2 流错误，需检查 CI 构建节点与 `repo.openeuler.org` 之间的网络链路（是否有代理/CDN 导致 HTTP/2 连接异常），或联系 openEuler 基础设施团队确认仓库服务状态。
2. 检查能否通过 `dnf` 配置（如 `/etc/dnf/dnf.conf`）在构建阶段暂时降级为 HTTP/1.1（`http2=false` 或 `http2=false` curl 选项），作为绕过 HTTP/2 服务端问题的应急方案——但这属于 CI Runner 配置层面调整，非 Dockerfile 层面修复。
