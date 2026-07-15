# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源传输中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, Error downloading packages

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方软件仓库在下载过程中出现 HTTP/2 帧层传输错误（`Curl error 92: INTERNAL_ERROR`），涉及 `gcc-gfortran`、`glibc-devel`、`guile`、`gcc` 等多个 RPM 包。DNF 耗尽所有可用镜像后，`gcc` 包最终下载失败，导致整个 `builder` 阶段构建中断。同时 `stage-1` 并行阶段（`#7`）因 BuildKit 级联取消机制被 `CANCELED`。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准格式的 Dockerfile（为 multiwfn 添加 openEuler 24.03-LTS-SP4 变体），Dockerfile 结构正确，使用的 `dnf install` 软件包均为 openEuler 24.03-LTS-SP4 仓库的标准包名。失败原因纯粹是构建时 openEuler 软件仓库的网络传输问题（HTTP/2 流异常），属于临时性基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 这是一个 CI 基础设施层面的临时网络故障。建议直接触发 CI 重跑（retry），在软件仓库恢复正常后构建应能通过。若多次重跑仍然失败，需排查 CI runner 到 `repo.****.org` 的网络链路或 openEuler 24.03-LTS-SP4 仓库状态。

## 需要进一步确认的点
- CI runner 所在网络环境到 openEuler 24.03-LTS-SP4 仓库的连通性是否正常（可在非 CI 环境中手动 `dnf install gcc` 验证）。
- 软件仓库端是否在该构建时间段内存在服务降级或维护。
- 其他使用相同基础镜像（`openeuler/openeuler:24.03-lts-sp4`）的 PR 是否也在同一时间段遭遇了类似的下载失败（若存在则可进一步确认为仓库端共性问题）。
