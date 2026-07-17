# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的软件仓库镜像在下载 RPM 包时持续返回 HTTP/2 流层错误（Curl error 92: Stream error in the HTTP/2 framing layer），dnf 在重试所有可用镜像后仍无法完成下载，最终导致 `dnf install` 失败（exit code: 1）。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个遵循现有格式的 Dockerfile（`cb37c53/24.03-lts-sp4/Dockerfile`）和对应的元数据更新（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令本身语法正确、包名有效（可从 #7 和 #8 的 `Dependencies resolved.` 阶段得到确认——dnf 成功解析了所有依赖并开始下载）。失败完全由 openEuler 24.03-LTS-SP4 上游软件仓库的 HTTP/2 传输层问题引起，属于 CI 基础设施/外部依赖问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 此失败是 openEuler 24.03-LTS-SP4 软件仓库镜像的临时性 HTTP/2 传输层故障（Curl error 92: INTERNAL_ERROR），与 PR 代码变更无关。等待仓库镜像恢复后，重新运行 CI 流水线即可通过。

### 方向 2（置信度: 低）
如果重试后持续出现同样错误，可考虑在 Dockerfile 的 `dnf install` 命令中添加重试参数（如 `--retries 10`）以容忍间歇性网络波动。但这仅能缓解症状，无法根治上游仓库的 HTTP/2 问题。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 软件仓库镜像（`repo.****.org`）的 HTTP/2 服务当前状态是否正常。
- 如果同样基于 openEuler 24.03-LTS-SP4 的其他镜像（非本次 PR 变更）在该时段也遇到类似 Curl error 92，则可进一步确认是仓库侧普遍性问题。
