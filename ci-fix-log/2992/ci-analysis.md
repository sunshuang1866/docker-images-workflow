# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, gcc-gfortran, gcc, glibc-devel, guile

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
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
- 失败原因: CI 构建环境中，dnf 从 `repo.****.org`（openEuler 24.03-LTS-SP4 官方仓库）下载 RPM 包时，多次遭遇 HTTP/2 流层协议错误（Curl error 92: INTERNAL_ERROR）。多个包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）均受影响，dnf 尝试所有镜像后仍失败，最终 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 下载失败导致整个 builder 阶段退出（exit code: 1），同时 stage-1（运行时阶段）被取消。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile 语法和逻辑正确（`dnf install` 包名均有效），编译器选择项（`sed` 替换 `ifort` 为 `gfortran` 等）也正确。失败根因是 openEuler 24.03-LTS-SP4 官方软件仓库在 CI 构建时出现 HTTP/2 协议层面的服务端异常。属于 CI 基础设施临时故障，与 PR 的 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 该失败是 CI 构建时的软件源临时网络故障，代码本身没有问题。在仓库网络恢复后重新触发 CI 构建即可通过。无需修改任何代码、Dockerfile 或元数据文件。

## 需要进一步确认的点
1. 确认 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库）当前是否恢复正常，可在 CI runner 上手动执行 `dnf download gcc-12.3.1-110.oe2403sp4.x86_64 --repo=OS` 验证。
2. 确认该仓库是否长期存在 HTTP/2 协议兼容性问题，如有必要可向基础设施团队反馈，建议仓库在服务端降级 HTTP/1.1 或修复 HTTP/2 流处理逻辑。
3. 如果该问题持续复现，可考虑在 Dockerfile 的 `dnf install` 前添加重试机制（如 `dnf install --retries 5 ...`），但该改动属于规避措施而非根因修复，不建议作为首选方案。
