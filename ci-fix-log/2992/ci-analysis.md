# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.****.org, No more mirrors to try

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（builder 阶段的 `RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像 `repo.****.org` 对多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）的下载请求返回 HTTP/2 协议层错误（`Curl error (92): Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2)`），dnf 重试耗尽所有镜像后，gcc 包下载失败导致整个 `dnf install` 步骤退出码 1

### 与 PR 变更的关联
此 PR 新增了一个针对 openEuler 24.03-LTS-SP4 的 Dockerfile（`Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`），Dockerfile 本身的语法和 `dnf install` 包列表均无问题。失败根因是 openEuler 24.03-LTS-SP4 仓库镜像在构建时段的 HTTP/2 协议层不稳定，导致间歇性包下载失败。该问题与 PR 代码变更无关，属于 CI 基础设施问题。

值得注意的是：stage-1（#7）也遭遇了相同的 `gcc-gfortran` 和 `glibc-devel` 下载失败，但 dnf 重试后成功恢复；builder 阶段（#8）需要下载更多包（157 个），其中 gcc-12.3.1 经过多次镜像重试后最终失败。

## 修复方向

### 方向 1（置信度: 中）
这是一个 `infra-error`，Code Fixer 无需处理。建议直接 **re-run CI**。由于该仓库镜像的 HTTP/2 问题可能为间歇性（stage-1 最终成功，builder 阶段大部分包也下载成功），重新触发构建有较高概率通过。若连续多次重试后仍失败，需排查 `repo.****.org` 的 HTTP/2 配置或考虑在 Dockerfile 中临时禁用 HTTP/2：

在 Dockerfile 的 `dnf install` 之前添加 `RUN echo "http2=false" >> /etc/dnf/dnf.conf` 强制 dnf 使用 HTTP/1.1 下载。

## 需要进一步确认的点
1. 构建时段 `repo.****.org` 的 HTTP/2 服务是否存在已知故障或维护窗口
2. 同日其他 openEuler 24.03-LTS-SP4 目标镜像的 CI 构建是否也出现同类 `Curl error (92)` 报错——若广泛出现则确认为仓库侧问题
3. stage-1（#7）的 gcc-gfortran 下载在两次 [MIRROR] 警告后是否真正下载成功（日志中 #7 最终被 CANCELED，无法确认其最终状态）
