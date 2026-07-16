# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: CI 构建环境中 `dnf` 从 openEuler 24.03-LTS-SP4 软件源下载 RPM 包（`gcc-gfortran`、`glibc-devel`、`gcc`、`guile`）时，多个仓库镜像返回 Curl error (92) HTTP/2 流错误（HTTP/2 stream was not closed cleanly: INTERNAL_ERROR），所有可用镜像均重试失败后 `dnf` 退出并返回错误码 1。两个并行构建阶段（#7 stage-1 和 #8 builder）均受同一类网络错误影响。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个合法有效的 Dockerfile（安装依赖集与已有的 `cb37c53-oe2403sp3` 完全一致，仅基础镜像从 `24.03-lts-sp3` 改为 `24.03-lts-sp4`），以及对应的 README、image-info.yml、meta.yml 元数据更新。失败原因是 openEuler 24.03-LTS-SP4 的软件源镜像在本次构建时出现 HTTP/2 层网络故障，属于 CI 基础设施问题，任何依赖该软件源的构建都将失败。

同一时间段的构建阶段 #7（stage-1，安装 `gcc-gfortran make openblas-devel lapack-devel`）也出现了相同的 HTTP/2 流错误（`gcc-gfortran`、`glibc-devel` 均报 Curl error 92），进一步佐证这是软件源侧的网络问题而非 Dockerfile 指令错误。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 CI 基础设施侧的网络问题，openEuler 软件源（`repo.****.org`）的某些镜像在 HTTP/2 协议层存在连接稳定性问题。建议在非高峰时段重试 CI 构建，或由 CI 运维团队排查 `repo.****.org` 的 HTTP/2 代理/负载均衡器配置。

### 方向 2（置信度: 中）
如果该 openEuler 24.03-LTS-SP4 软件源持续不稳定，可考虑在 Dockerfile 的 `dnf install` 前增加 dnf 配置，禁用 HTTP/2（`http2=false`）回退到 HTTP/1.1，或配置重试/超时参数以提高网络容错性。但这属于基础设施规避措施而非根因修复。

## 需要进一步确认的点
- 确认 `repo.****.org` 软件源在当前时间段是否有已知的服务中断或维护
- 确认同一时间段其他依赖 openEuler 24.03-LTS-SP4 软件源的 PR 构建是否也遇到了相同的 HTTP/2 流错误
- 确认 CI runner 节点到 `repo.****.org` 的网络路径是否稳定（可能是中间代理或 CDN 节点问题）
