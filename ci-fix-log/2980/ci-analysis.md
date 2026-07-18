# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP2流错误
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
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在 HTTP/2 传输层反复出现流错误（`Curl error 92: HTTP/2 stream INTERNAL_ERROR`），导致 `cmake-data`、`git-core` 和 `gcc-c++` 三个包下载失败。其中 `gcc-c++` 经多次重试（两个不同 stream ID：65 和 83）后仍失败，`dnf` 耗尽所有可用镜像后报错退出。这是一个**典型的 CI 基础设施/网络层问题**，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关。** PR 仅新增了一个标准的 Grads Dockerfile（含常规 `dnf install` 构建依赖列表）及配套的 `README.md`、`image-info.yml`、`meta.yml` 元数据文件。Dockerfile 中的包列表与同仓库其他 Grads 版本（如 `24.03-lts-sp3`）一致，语法正确。失败发生在 `dnf` 从远程 RPM 仓库下载包阶段，属于下游镜像站网络传输问题，这是唯一新引入的 Dockerfile 面临该仓库源的问题。

## 修复方向

### 方向 1（置信度: 低）
在 Dockerfile 的 `dnf install` 命令中添加 `--retries 5` 参数和 `--setopt=timeout=30` 超时配置，提高对间歇性 HTTP/2 流错误的容忍度。但需注意：该方案不能根本解决镜像站侧 HTTP/2 传输问题，尤其是当问题持续存在时（日志中 `gcc-c++` 在两次不同 stream 上均失败）依然可能失败。

### 方向 2（置信度: 低）
在 `dnf install` 之前将 repo 配置中的 HTTP/2 降级为 HTTP/1.1（通过 `--setopt=ip_resolve=4` 或修改 repo 文件添加 `http2=false`），规避 openEuler 镜像站在 HTTP/2 层的不稳定性。但此方法的有效性取决于镜像站是否正确实现了 HTTP/1.1 fallback。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 镜像站（repo.****.org）的 HTTP/2 流错误是否为持续性故障还是间歇性问题。建议在 CI 中重试该 job，若多次重试均在同一批包（`gcc-c++`、`cmake-data`、`git-core`）上失败，则问题偏向镜像站侧；若每次失败在不同包上，则为网络层间歇性抖动。
- 同一 CI 环境中针对 `24.03-lts-sp3` 基础镜像的构建是否也存在同样问题（从日志看 sp3 构建本次未触发，无法对比）。
- CI runner 所在网络环境与 `repo.****.org` 之间是否存在中间代理或防火墙干扰 HTTP/2 长连接。
