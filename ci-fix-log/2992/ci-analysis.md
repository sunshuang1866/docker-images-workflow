# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: dnf仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success

ERROR: failed to solve: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库（`repo.****.org`）在构建时段存在 HTTP/2 流传输异常，多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`gcc`、`guile`）下载过程中遭遇 `Curl error (92): Stream error in the HTTP/2 framing layer`，dnd 重试所有镜像后最终放弃，构建失败。该错误同时发生在 builder 阶段（#8）和 runtime 阶段（#7），确认是仓库端网络问题而非 Dockerfile 问题。

### 与 PR 变更的关联
**与 PR 改动无关。** PR 仅新增了一个结构标准的 Dockerfile（基于已有 `24.03-lts-sp3` 模板适配 `24.03-lts-sp4`），以及对应的 README、image-info.yml、meta.yml 条目。`dnf install` 安装的包名与已有 `24.03-lts-sp3` 版本完全一致，失败的直接原因是 openEuler 24.03-LTS-SP4 的软件仓库在构建时段出现 HTTP/2 连接异常。这是 CI 基础设施/外部依赖问题，非代码缺陷。Code Fixer 无需对 Dockerfile 做任何修改。

## 修复方向

### 方向 1（置信度: 低）
**等待仓库恢复后重试。** 该失败属于 transient infrastructure error（暂时性基础设施错误），openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 服务端问题在构建时段发生。唯一可行的处理方式是等待仓库恢复，然后重新触发 CI 构建。建议观察其他使用同一仓库的 PR 构建是否也出现相同错误来确认。

### 方向 2（无）
不存在与代码相关的修复方向。

## 需要进一步确认的点
1. **确认仓库状态**：检查 `repo.****.org`（openEuler 24.03-LTS-SP4 官方仓库）在构建时段（2026-07-09 14:46-14:50 UTC 前后）是否存在服务端 HTTP/2 故障或网络抖动。
2. **确认是否普遍**：检查同期其他以 `24.03-lts-sp4` 为基础镜像的 PR 构建是否出现相同的 `Curl error (92)` 错误，以排除 openEuler 24.03-LTS-SP4 仓库的批量故障。
3. **重试构建验证**：重新触发 CI（`recheck` 或新 push），如果构建成功，则确认本失败为暂时性基础设施问题。
