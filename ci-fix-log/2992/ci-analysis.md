# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, [MIRROR], [FAILED], No more mirrors to try, dnf install

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的软件源（`repo.****.org`）在 HTTP/2 下载期间频繁出现流错误（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），波及多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`），最终 `gcc` 包在所有镜像源重试均失败后无法下载，导致 `dnf install` 退出码为 1。这是 CI 构建环境中软件仓库源 HTTP/2 协议层面的网络基础设施问题。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个面向 openEuler 24.03-lts-sp4 的 Dockerfile，其中 `dnf install` 安装的均为标准仓库包（`git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel`），包名和版本均正确无误。错误完全源于 `repo.****.org`（openEuler 24.03-LTS-SP4 官方仓库镜像）在 HTTP/2 协议层面服务不稳定，多个独立 HTTP/2 stream 被服务端非正常关闭（`INTERNAL_ERROR`），属于 CI 基础设施侧的网络/服务端问题。

日志中两个独立 Docker 构建阶段（builder #8 和 runtime #7）均反复遭遇同一错误，进一步佐证这是仓库源端问题而非单次偶然事件。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 openEuler 24.03-LTS-SP4 软件仓库源的 HTTP/2 服务端问题，应在 CI 基础设施层面处理：
- 等待仓库源恢复后重新触发 CI（如果问题是临时性的）
- 或在 CI 的 dnf 配置中切换到备用镜像源
- 或在 dnf 配置中禁用 HTTP/2 回退到 HTTP/1.1（如设置 `http2=false` 或 `/etc/dnf/dnf.conf` 中添加 `ip_resolve=4`）

## 需要进一步确认的点
- `repo.****.org` 是否在报告时间段存在已知的服务端 HTTP/2 协议问题或服务中断
- 其他使用同一 openEuler 24.03-LTS-SP4 仓库源的 PR 是否在相同时段也遭遇了相同错误（用于确认是临时性中断还是持久性问题）
- 是否需要为 `dnf install` 操作添加重试机制（如 `--retries`）或在 Dockerfile 层面增加容错
