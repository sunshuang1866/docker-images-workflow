# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流中断
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 DNF 软件仓库（`repo.****.org`）在 HTTP/2 下载过程中反复出现流中断（`Curl error (92): Stream error in the HTTP/2 framing layer`），多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）均受影响，最终 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 耗尽所有镜像重试后下载失败。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 仅新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（47 行）、更新 `meta.yml`（+2 行）、更新 `README.md` 和 `image-info.yml`（各 +1 行）。Dockerfile 的 `dnf install` 命令语法正确，失败原因是 openEuler 24.03-LTS-SP4 软件仓库服务器在 HTTP/2 协议层面不稳定，属于 CI 基础设施/上游仓库侧的瞬态网络故障。PR 代码本身没有问题。

## 修复方向

### 方向 1（置信度: 低）
**直接重试构建**。由于该失败是 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 服务器侧瞬态故障，最可能的情况是重跑 CI 即可通过。若重试仍然失败，则表明仓库侧存在持续性问题。

### 方向 2（置信度: 低）
若仓库 HTTP/2 问题是持续性的，可在 Dockerfile 的 `dnf install` 之前添加 `dnf config-manager` 配置，为该仓库禁用 HTTP/2 或增加重试次数/超时时间，以绕过 HTTP/2 流中断问题。但这不是 PR 代码的缺陷，而是对上游仓库不稳定性的防御性适配。

## 需要进一步确认的点
- 该仓库是否被多次构建都因同一原因失败（若仅此一次，则是瞬态故障，直接重跑即可）
- 其他使用 `openEuler 24.03-lts-sp4` 基础镜像的 Dockerfile（如 `Others/multiwfn/cb37c53/24.03-lts-sp3/Dockerfile`）在同时段是否也出现类似报错，以判断是全局性 repo 问题还是特定于 x86-64 构建节点
- `repo.****.org` 实际的域名是什么，是否有备用镜像站可以切换
