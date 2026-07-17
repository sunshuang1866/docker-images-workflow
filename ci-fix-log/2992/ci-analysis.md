# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.***.org, dnf install, rpm download, INTERNAL_ERROR (err 2)

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 RPM 仓库镜像服务器（`repo.***.org`）在处理 HTTP/2 连接时反复出现流错误（`Stream error in the HTTP/2 framing layer, INTERNAL_ERROR`），导致 `gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等多个基础构建包的 RPM 下载失败。dnf 重试了所有可用镜像后仍无法成功下载，最终 `exit code: 1`。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个标准 Dockerfile（定义构建 MultiWFN 在 openEuler 24.03-LTS-SP4 上的镜像），Dockerfile 中的 `dnf install` 命令语法正确、包名有效。失败原因是 RPM 仓库服务器端的 HTTP/2 协议问题——两个 Docker 构建阶段（#7 运行时阶段和 #8 构建阶段）在下载不同包时均遭遇相同类型的流错误。这是 CI 基础设施层的网络问题，不影响 Dockerfile 的正确性。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 openEuler RPM 仓库镜像服务器的临时性 HTTP/2 故障（`INTERNAL_ERROR (err 2)`）。建议：
- 等待仓库服务恢复后触发 CI 重跑（retry build）。
- 如果问题持续出现，可考虑在 Dockerfile 的 `RUN dnf install` 前禁用 HTTP/2 或配置 `curl` 降级到 HTTP/1.1，但通常服务器侧修复后即可恢复正常。

## 需要进一步确认的点
- 确认 `repo.***.org`（openEuler 24.03-LTS-SP4 仓库）当前是否在维护或已知存在 HTTP/2 故障。
- 如果多次 retry 后仍然失败，检查是否需要为 CI 构建环境配置备选 RPM 镜像源。

## 修复验证要求
（不适用——本次为 infra-error，与 PR 代码无关，无需 code-fixer 进行代码修改。）
