# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2传输中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, [FAILED], No more mirrors to try

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
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`
- 失败原因: CI 构建环境在执行 `dnf install` 从 openEuler 24.03-LTS-SP4 官方 repo 下载 RPM 包时，多次遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），所有镜像源重试均失败，最终 `gcc-12.3.1-110.oe2403sp4.x86_64` 下载失败导致构建终止。Stage-1 构建 (`#7`) 也遇到同类错误（`glibc-devel`、`gcc-gfortran`），随后被 CANCELED。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 Multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（以及配套的 README、image-info.yml、meta.yml 更新），Dockerfile 中 `dnf install` 的包列表和语法均正确。失败根因是 CI 构建节点在下载 RPM 包时与 openEuler 软件仓库之间发生了 HTTP/2 协议层通信错误，属于纯粹的 CI 基础设施/网络问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施故障（HTTP/2 流错误），建议重试 CI 构建。若反复出现，需排查：
- CI 构建节点到 `repo.****.org`（openEuler 镜像站）的网络链路稳定性
- 镜像站端 HTTP/2 服务的健康状况或负载
- 是否需要为 `dnf` 配置降级到 HTTP/1.1（通过 `dnf.conf` 设置 `http2=false` 或 `ip_resolve=4`）

### 方向 2（可选）
若 CI 重试后依然失败且确认是 repo 端问题，可考虑在 Dockerfile 中为 `dnf install` 添加 `--setopt=retries=10` 增加重试次数以应对偶发网络抖动。

## 需要进一步确认的点
- CI 构建环境（`ecs-build-docker-x86-03-sp`）与 openEuler 24.03-LTS-SP4 镜像站之间的网络连通性是否稳定
- 同一时间段内其他 PR 中涉及 `dnf install` 从 SP4 repo 下载包的构建是否也出现相同错误（判断是系统性 repo 问题还是单次偶发）
- 该 repo 镜像站是否需要 HTTP/1.1 fallback
