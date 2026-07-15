# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success

ERROR: failed to solve: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 DNF 软件仓库镜像在 HTTP/2 下载过程中发生流传输错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致 `gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等多个 RPM 包下载失败，最终 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 在所有镜像源重试均失败后，`dnf install` 命令以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该失败属于 CI 基础设施问题：

1. PR 仅新增了一个合法的 Dockerfile（`cb37c53/24.03-lts-sp4/Dockerfile`）及相关元数据文件，Dockerfile 语法正确、软件包列表合理（与已有的 SP3 版本 Dockerfile 模式一致）。
2. 失败的直接原因是 openEuler 24.03-LTS-SP4 的 DNF 仓库镜像在构建时段存在 HTTP/2 流传输不稳定问题，6 个不同的 HTTP/2 stream（31, 17, 37, 15, 43, 27）均报 `INTERNAL_ERROR`，表明这是服务端镜像基础设施的系统性网络问题。
3. 两个构建阶段（builder 阶段 #8 和最终运行阶段 #7）均受到相同类型的 HTTP/2 流错误影响，进一步佐证问题出在仓库侧而非 Dockerfile 或网络策略。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败为临时性网络基础设施问题，Dockerfile 和 PR 变更本身没有错误。可通过 `/retest` 或类似方式重新触发 CI 流水线，在 openEuler 24.03-LTS-SP4 仓库镜像恢复稳定后构建即可成功。

### 方向 2（置信度: 低）
如果重试后仍然失败，且确认是 SP4 仓库镜像持续不稳定，可考虑在 Dockerfile 的 `dnf install` 命令前添加 `dnf config-manager --setopt=timeout=60 --save` 或降低 HTTP/2 到 HTTP/1.1（`echo "http2=false" >> /etc/dnf/vars/http2`），但这些属于 workaround 而非根因修复。

## 需要进一步确认的点
- 检查 openEuler 24.03-LTS-SP4 软件仓库在 CI 构建时段（2026-07-09 14:46-14:47 UTC）是否存在已知的服务端网络故障或维护窗口。
- 确认同一时段内其他使用 `openeuler:24.03-lts-sp4` 基础镜像的 PR 构建是否也出现相同的 DNF 下载失败，以排除 PR 特定配置问题。
