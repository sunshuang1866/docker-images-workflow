# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM 仓库 HTTP/2 传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在 HTTP/2 传输层反复出现 `INTERNAL_ERROR`（Curl error 92），导致 `gcc`、`gcc-gfortran`、`guile` 等多个包下载失败，最终 `gcc-12.3.1-110.oe2403sp4.x86_64` 耗尽所有重试镜像后构建中止。同为 SP4 仓库的 stage-1（#7）也出现同类 Curl error 92（`glibc-devel`、`gcc-gfortran`），但因下载包数较少（32 vs 157），受影响面相对小。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增 Multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据。失败发生在新 Dockerfile 的 `dnf install` 阶段，错误是远程 RPM 仓库的 HTTP/2 协议层故障（服务端返回 `INTERNAL_ERROR`），属于 CI 基础设施/外部依赖问题。PR 中的 Dockerfile 语法和包名均正确无误。

## 修复方向

### 方向 1（置信度: 高）
**无需修复 PR 代码，重试 CI 构建即可。** 该失败是 openEuler 24.03-LTS-SP4 RPM 镜像仓库临时的 HTTP/2 服务端协议错误。若多次重试仍持续失败，需联系 openEuler 基础设施团队排查 repo 服务器的 HTTP/2 配置或负载均衡问题。

### 方向 2（置信度: 低）
若仓库 HTTP/2 问题短期无法解决，可考虑在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或设置 `ip_resolve=4` 等 dnf 配置来绕过 HTTP/2 传输层问题，但这属于规避手段而非根因修复。

## 需要进一步确认的点
- 该 CI 构建失败为单次现象还是持续复现（可触发 rerun 验证）
- openEuler 24.03-LTS-SP4 仓库服务端 HTTP/2 是否已知存在稳定性问题
- 同一时段其他使用 SP4 基础镜像的 PR 是否也出现同类 Curl error 92
