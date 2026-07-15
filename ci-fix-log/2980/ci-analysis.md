# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y       gcc gcc-c++ make cmake ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 镜像仓库（`repo.****.org`）在多个 HTTP/2 连接上间歇性地返回流层错误（Curl error 92: `INTERNAL_ERROR`），导致 `gcc-c++` 等包下载重试耗尽后失败。同一构建中其他大部分包下载成功，但 `cmake-data`、`git-core` 和 `gcc-c++` 三个包均遇到 HTTP/2 流错误，其中 `gcc-c++` 在两个不同流上均失败，最终所有镜像均不可用。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个 GrADS 2.2.3 的 Dockerfile（标准 `dnf install` 构建依赖 + `git clone` + `autoreconf && make` 流程）以及三条元数据更新（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法正确、包名无错误（258 个包均被 dnf 解析并列入安装计划），失败完全由 openEuler 镜像仓库服务端的 HTTP/2 连接异常导致。该构建在镜像仓库正常时预期可以通过。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 该失败是 openEuler 24.03-LTS-SP4 镜像仓库的临时网络/服务端问题（HTTP/2 流层 INTERNAL_ERROR）。建议重新触发 CI 构建，让 `dnf` 在镜像仓库恢复正常时重新下载。若问题持续出现，可在 Dockerfile 的 `dnf install` 命令中添加 `--retries 10` 参数增加下载重试次数，提高对间歇性网络波动的容忍度。

### 方向 2（置信度: 低）
若镜像仓库问题长期无法解决，可考虑在 Dockerfile 中为 `dnf` 添加 `--setopt=timeout=30` 参数降低单次连接超时时间以加速重试，或通过 `curl -L` 手动下载关键的 `gcc-c++` 包缓存到本地再安装。但这两种方案都是规避而非根治手段，不建议在未确认仓库持续性故障前采用。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的 OS 仓库在 CI 构建时段是否存在已知的网络故障或维护窗口。
- 若同类 `Curl error (92)` 在其他 PR 的 24.03-LTS-SP4 构建中也频繁出现，说明该仓库服务端存在 HTTP/2 实现的稳定性缺陷，需要运维侧排查。
- 确认 `repo.****.org` 具体对应哪个实际镜像站域名，是否存在镜像站点间的 HTTP/2 实现差异（某些站点对 HTTP/2 的支持不完善）。
