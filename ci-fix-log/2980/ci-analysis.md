# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`:6（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的官方 RPM 仓库镜像（`repo.***.org`）在提供 HTTP/2 下载服务时出现流错误（`Stream error in the HTTP/2 framing layer: INTERNAL_ERROR (err 2)`），导致多个 RPM 包（cmake-data、git-core、gcc-c++）下载失败。`gcc-c++` 包多次重试均失败，最终 `dnf` 耗尽所有镜像后报错退出。这是一个纯粹的 CI 基础设施/仓库镜像侧的网络故障。

### 与 PR 变更的关联

**与 PR 变更无关。** 本次 PR 仅新增了一个 Dockerfile 文件（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）以及三个元数据文件（README.md、doc/image-info.yml、meta.yml）的条目更新。失败的 `dnf install` 步骤发生在从 openEuler 官方仓库下载系统软件包的过程中，这是 CI 构建环境的网络/镜像站问题，PR 代码本身没有任何问题。Dockerfile 中列出的包名均为 openEuler 24.03-LTS-SP4 仓库中的合法包名。

258 个包中有 255 个下载成功（日志中可见大量 `Installing:` 和已下载包列表），仅个别大文件包（如 13 MB 的 `gcc-c++`、11 MB 的 `git-core`、2.1 MB 的 `cmake-data`）因仓库镜像 HTTP/2 连接不稳定而失败，进一步印证这是网络层间歇性问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 这是一个临时性的基础设施网络故障（openEuler 仓库镜像 HTTP/2 流中断），与 PR 代码无关。等待仓库镜像恢复后重新触发 CI 构建即可通过。无需修改任何代码。

### 方向 2（置信度: 中）
如果多次重试仍然失败，可考虑在 Dockerfile 中为 `dnf install` 添加重试机制（如 `dnf install -y --setopt=retries=10 ...`），或尝试使用其他可用镜像源。但鉴于大部分包已下载成功、仅少数大文件受 HTTP/2 流不稳定影响，这更倾向于是临时性问题。

## 需要进一步确认的点

- openEuler 24.03-LTS-SP4 的仓库镜像 `repo.***.org` 在 CI 构建时段是否存在已知的 HTTP/2 服务异常或网络动荡。
- 同一时段是否有其他使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 也遇到相同的 `Curl error (92)` 下载失败。
