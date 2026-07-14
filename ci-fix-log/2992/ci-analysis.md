# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install` 步骤，builder 阶段）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在 CI 构建期间出现 HTTP/2 协议层错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致多个包（gcc-gfortran、glibc-devel、guile、gcc）下载失败。其中 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 在所有可用镜像上均重试失败，`dnf install` 以 exit code 1 中止。构建中的另一个并行阶段（stage-1, #7）同样遭遇了 `glibc-devel` 和 `gcc-gfortran` 的 HTTP/2 流错误，虽通过重试绕过部分失败，但在 builder 阶段失败后被取消（CANCELED）。

### 与 PR 变更的关联
**与 PR 无关。** PR 的变更仅为新增 Multiwfn 的 openEuler 24.03-LTS-SP4 Dockerfile 及相关元数据和文档条目。Dockerfile 的结构与同项目其他版本（如 sp3 版本）一致，`dnf install` 的包列表语法正确。失败原因完全是 openEuler 24.03-LTS-SP4 RPM 仓库镜像在构建期间出现 HTTP/2 协议层面不稳定，属 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**等待仓库镜像恢复后重试 CI。** 该失败是 openEuler 24.03-LTS-SP4 官方 RPM 镜像仓库的临时性 HTTP/2 协议层不稳定所致，与 PR 代码变更无关。建议在仓库镜像恢复正常后重新触发 CI 构建（re-run failed jobs），无需任何代码修改。

### 方向 2（置信度: 低）
**降级到 HTTP/1.1 绕过 HTTP/2 问题。** 若该仓库镜像的 HTTP/2 问题持续存在，可考虑在 Dockerfile 的 `RUN dnf install` 之前配置 dnf 或 curl 强制使用 HTTP/1.1（如设置 `http_version=HTTP_1_1` 或 `--http1.1`）。但这属于 workaround 而非根本修复，且可能影响下载速度。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像当前是否已恢复稳定（可直接访问下载 URL 验证）
- 确认其他基于 openEuler 24.03-LTS-SP4 的镜像构建在该时间段是否也出现同类错误（判断是全局性镜像故障还是仅影响该 job 的网络链路问题）
- 确认构建 runner 节点 `ecs-build-docker-x86-03-sp` 到仓库镜像的网络连通性是否正常

## 修复验证要求
无需修复验证（infra-error，不涉及代码修改）。若重试 CI 后仍失败，需获取下游架构构建 job 的完整日志以确认是否同一仓库镜像问题跨架构复现。
