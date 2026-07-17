# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.*.org

## 根因分析

### 直接错误
```
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
------
Dockerfile:7
--------------------
   6 |     
   7 | >>> RUN dnf install -y \
   8 | >>>       git gcc gcc-c++ gcc-gfortran make \
   9 | >>>       openblas-devel lapack-devel && \
  10 | >>>     dnf clean all
--------------------
ERROR: failed to solve: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）的 HTTP/2 服务器在该时间点存在协议层故障，Curl 下载多个 RPM 包时持续遭遇 HTTP/2 流未干净关闭的错误（Curl error 92: INTERNAL_ERROR），导致 `gcc`、`gcc-gfortran`、`guile`、`glibc-devel` 等多个包的镜像重试均失败，最终 `dnf install` 返回 exit code 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个标准的多阶段构建 Dockerfile（安装 gcc、gcc-gfortran、openblas-devel 等构建依赖后编译 Multiwfn），以及对应的 meta.yml、README.md 和 image-info.yml 更新。Dockerfile 的 `dnf install` 命令写法与同项目其他 Dockerfile 一致，语法正确。构建失败纯粹因为 CI 运行时 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像出现 HTTP/2 协议层故障，导致大量 RPM 包下载失败。

该结论的额外证据：
1. 两个独立构建阶段（builder #8 和 runtime #7）同时遭遇相同的 Curl error (92)，说明此非单个下载任务的偶发问题，而是仓库侧的普遍问题。
2. 受影响的包横跨多个不同 RPM（gcc、gcc-gfortran、guile、glibc-devel），排除了个别包损坏的可能性。
3. 失败信息 `No more mirrors to try` 表明 dnf 已尝试了所有可用镜像，均因 HTTP/2 流错误而失败。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 此失败为 `infra-error`——openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务暂时性故障。应通过 CI 平台重新触发构建（retry）。若反复出现同类错误，说明 `repo.****.org` 镜像站与 CI 构建环境之间存在持续的网络协议不兼容（如中间代理/防火墙不支持 HTTP/2），届时需由基础设施团队排查网络链路或将 dnf 仓库源切换为 HTTP/1.1 协议。

## 需要进一步确认的点
- 重新触发一次 CI build，确认是否为暂时性网络故障。若重试后成功，则无需任何修复。
- 若多次重试均失败，需排查 CI 构建环境到 `repo.****.org` 镜像站的网络链路中是否存在 HTTP/2 协议不兼容的中间设备（如代理、防火墙）。
- 可对比 openEuler 24.03-LTS-SP4 的 `repo.openeuler.org` 官方镜像站在同一时间点是否可用（目前日志中被屏蔽的域名可能是内部镜像）。
