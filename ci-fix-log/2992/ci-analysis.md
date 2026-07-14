# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, INTERNAL_ERROR (err 2)

## 根因分析

### 直接错误

```
#8 [builder 2/5] RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel && dnf clean all

> [builder 2/5] RUN dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all:

1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
1830.2 Error: Error downloading packages:
1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
------
Dockerfile:7-10
ERROR: failed to solve: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

更早的 HTTP/2 流错误分布在构建时间线多处，涉及多个大型包：

```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92) [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92) [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92) [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92) [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（新增 Dockerfile 的 `dnf install` 步骤）
- 失败原因: 构建过程中，`dnf install` 从 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库）下载大型 RPM 包（gcc 34MB、gcc-gfortran 13MB、guile 6.3MB、glibc-devel 2.0MB）时，仓库服务器多次返回 HTTP/2 流帧错误 `Curl error (92): INTERNAL_ERROR (err 2)`。其中 gcc 包（34MB）在 builder 阶段耗尽所有镜像重试后仍然失败，导致整个构建流程中断。

### 与 PR 变更的关联

**与 PR 变更无关。** 本次 PR 仅新增了 `sp4` 版本的 Dockerfile（从已有的 `sp3` 版本 Dockerfile 移植而来）以及对应的文档/元数据更新。Dockerfile 本身语法正确、依赖声明合理（与 sp3 版本一致）。失败是 openEuler 24.03-LTS-SP4 仓库镜像站的 HTTP/2 基础设施不稳定造成的偶发性网络故障，与 PR 的代码改动没有任何关系。

受影响的两个并行构建阶段：
- 构建阶段（builder, #8）：安装 157 个包，gcc 34MB 包下载彻底失败
- 运行时阶段（stage-1, #7）：安装 32 个包，部分包遇 HTTP/2 错误但重试后恢复，最终因 builder 阶段先失败而被 CANCELED

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI**。这是 openEuler 24.03-LTS-SP4 仓库镜像站临时的 HTTP/2 服务不稳定问题，与代码无关。等待仓库镜像恢复正常后重新运行 CI 流水线即可通过。

### 方向 2（置信度: 低）
若多次重试仍然在同一批包上失败，可考虑在 Dockerfile 中为 `dnf install` 添加 `--retries N` 参数（默认重试次数可能不足以覆盖间歇性故障），或更换 `dnf.conf` 中的 baseurl 为更稳定的镜像站。

## 需要进一步确认的点

1. 确认 `repo.****.org` 的具体域名和服务商，判断是否为仓库侧已知的 HTTP/2 稳定性问题
2. 若同一时间点其他 PR 也在 24.03-LTS-SP4 仓库下载大包时遇到相同错误，可确认是仓库侧全局故障
3. 观察该仓库的 HTTP/2 稳定性历史——如果频繁出现，可能需要联系仓库运维调整服务器 HTTP/2 配置或提供回退到 HTTP/1.1 的选项
