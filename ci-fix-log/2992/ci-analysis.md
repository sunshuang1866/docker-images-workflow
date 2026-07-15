# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, [MIRROR], No more mirrors to try, dnf install

## 根因分析

### 直接错误

```
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1

ERROR: failed to solve: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: CI 构建环境在通过 `dnf` 从 openEuler 24.03-LTS-SP4 软件仓库下载 RPM 包时，多个包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）反复遭遇 HTTP/2 帧层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），经过多次重试后 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 耗尽所有镜像重试次数，导致 `dnf install` 整体失败。同时，runtime 阶段（stage #7）的 `dnf install` 也出现了相同的 `[MIRROR]` 错误，但因 builder 阶段先触发致命失败而被取消。

### 与 PR 变更的关联

PR 变更与本次失败**无关**。PR 仅新增了一个标准格式的 Dockerfile（`dnf install` 命令写法正确，与同项目其他已成功的 Dockerfile 一致）和配套的 README.md、image-info.yml、meta.yml 更新。失败的直接原因是 openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）在处理 HTTP/2 请求时反复出现流中断，属于 CI 基础设施/上游仓库的网络问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。该错误是 openEuler 软件仓库的瞬时 HTTP/2 服务端问题，与 PR 代码变更无关。等待仓库恢复后重新触发 CI pipeline 即可通过。

（Code Fixer 无需处理）

## 需要进一步确认的点

- 确认 openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）当前的服务状态是否正常，是否存在已知的 HTTP/2 代理/负载均衡器问题。
- 如果重试后多次仍出现相同错误，需要确认 CI runner（`ecs-build-docker-x86-03-sp`）到 `repo.****.org` 的网络链路是否稳定，以及该 runner 上其他构建是否也遇到相同问题。
