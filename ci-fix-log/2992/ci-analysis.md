# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输异常
- 新模式症状关键词: Curl error (92), Stream error, HTTP/2 framing layer, INTERNAL_ERROR, dnf install, No more mirrors to try

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
------
ERROR: failed to solve: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel` 步骤）
- 失败原因: dnf 从 openEuler 24.03-LTS-SP4 仓科镜像站（`repo.****.org`）下载 RPM 包时，多个包（gcc-gfortran、glibc-devel、guile、gcc）反复遭遇 HTTP/2 协议层传输错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），dnf 重试所有可用镜像均失败，最终 `No more mirrors to try`，构建中止。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 本身结构正确——基础镜像拉取成功、元数据校验通过、dnf 仓库索引加载正常。失败发生在 dnf 实际下载 RPM 包的阶段，系 openEuler 24.03-LTS-SP4 仓库镜像站的 HTTP/2 传输层问题导致的纯网络/基础设施故障。两个并发构建阶段（builder #8 和 stage-1 #7）均遭遇同类 HTTP/2 stream 错误，进一步确认这是仓库服务端的协议层异常，而非 Dockerfile 或构建逻辑缺陷。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 该失败为基础设施层 HTTP/2 传输异常，属于间歇性网络问题而非代码缺陷。直接重新触发 CI 流水线（re-run），大概率可通过。若多次重试仍失败，需联系 openEuler 24.03-LTS-SP4 仓库镜像站运维排查 HTTP/2 服务端配置。

## 需要进一步确认的点
- 该 `repo.****.org` 仓库镜像站是否为内部代理/缓存层，是否存在 HTTP/2 配置问题（如 stream 并发限制过低、连接复用策略不当）。
- openEuler 24.03-LTS-SP4 仓库是否在 CI 构建时段存在服务不稳定（可查看其他使用同一基础镜像的构建 job 是否也出现同类错误）。
- 若多次重试仍然失败，确认是否有替代的镜像源 URL 可用（如直接指向 `repo.openeuler.org`）。
