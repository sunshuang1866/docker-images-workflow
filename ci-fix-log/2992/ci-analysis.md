# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error, HTTP/2 framing layer, INTERNAL_ERROR, err 2, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y   git gcc gcc-c++ gcc-gfortran make   openblas-devel lapack-devel && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包镜像仓库在 CI 构建时刻发生 HTTP/2 协议层流错误（Curl error 92, INTERNAL_ERROR），导致 `gcc`、`gcc-gfortran`、`guile`、`glibc-devel` 等多个 RPM 包下载失败，dnf 耗尽所有重试镜像后报错退出。

### 与 PR 变更的关联
PR 变更与本次失败**无直接因果关系**。新增的 Dockerfile 本身语法和逻辑正确（`dnf install` 命令格式与同仓库已有的 SP3 版本一致），但由于该 PR 是仓库中**首次引入 24.03-LTS-SP4 为基础镜像**的 multiwfn 构建，dnf 需要下载 openEuler 24.03-LTS-SP4 专属的 157 个 RPM 包（不同于已有的 SP3 构建），大量下载请求暴露了 SP4 镜像仓库的 HTTP/2 协议稳定性问题。

值得注意的是，同一构建中 stage-1（`#7`）也遭遇了 `glibc-devel` 和 `gcc-gfortran` 的 HTTP/2 流错误，但最终通过重试恢复；builder stage（`#8`）因下载包数量更多（157 个 vs 32 个），在 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`（34MB 大文件）上重试多次后最终耗尽所有镜像而失败。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，与 PR 代码无关。失败原因是 openEuler 24.03-LTS-SP4 镜像仓库在特定时刻的 HTTP/2 协议栈不稳定。**无需修改 Dockerfile 或任何代码**，建议触发 CI 重跑（retry），在镜像仓库恢复稳定后构建即可通过。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 官方仓库（`repo.openeuler.org` 或配置的镜像站）是否在 CI 失败时段存在已知的 HTTP/2 服务端问题
- 若同一时段其他 PR（使用 SP4 基础镜像的）也失败，可进一步确认是仓库侧问题而非 PR 引入
- 若多次重试均失败，可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager --setopt max_parallel_downloads=1` 降低并发连接数以规避 HTTP/2 流竞争，或强制 dnf 使用 HTTP/1.1 协议
