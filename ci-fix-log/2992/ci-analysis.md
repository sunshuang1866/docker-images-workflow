# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

在此之前，多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`）均在下载过程中遭遇相同的 HTTP/2 stream 错误，最终 `gcc`（34MB 的大包）耗尽所有镜像重试后导致构建终止。Docker 并发多阶段构建的两个 stage（builder 157 个包、stage-1 32 个包）同时向同一仓库发起 HTTP/2 下载请求，均出现不同程度的 stream 中断（`err 2: INTERNAL_ERROR`）。

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库（`repo.****.org`）在通过 HTTP/2 协议传输大型 RPM 文件时，服务端频繁发出 `INTERNAL_ERROR` 流重置，导致 curl（dnf 底层下载器）多次重试后仍然失败。两个并发构建阶段同时下载进一步加剧了连接压力。

### 与 PR 变更的关联
PR 变更**与 CI 失败无直接因果关系**。PR 仅在以下文件中做了纯增量的文档和配置变更：
- 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（标准多阶段构建，dkf install 依赖列表正确）
- 更新 `Others/multiwfn/README.md`、`Others/multiwfn/doc/image-info.yml`、`Others/multiwfn/meta.yml`

Dockerfile 中的 `dnf install` 包列表、sed 替换命令和 git clone 逻辑均语法正确、无逻辑缺陷。失败根因是 openEuler 24.03-LTS-SP4 仓库服务端的 HTTP/2 流控制问题，与镜像构建代码无关。

## 修复方向

### 方向 1（置信度: 低）
**等待仓库恢复 / 重试 CI** — 这是基础设施侧的临时性问题。若仓库提供商修复了 HTTP/2 流控制问题，同样的构建可自然通过。建议在非高峰时段重试 CI。

### 方向 2（置信度: 低）
**在 Dockerfile 中添加 `dnf` 重试/超时参数增强容错** — 通过设置 `dnf.conf` 的 `max_retries`、`timeout`、`minrate` 或强制使用 HTTP/1.1（`http2=false`）来规避 HTTP/2 协议错误。但此方案只治标不治本，且不确定 CI 环境是否支持 HTTP/1.1 回退。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）的 HTTP/2 服务是否存在已知问题，是否有其他 PR 在构建 SP4 镜像时遇到同类错误。
- CI 构建环境中是否配置了 HTTP/2 代理，代理层是否引入了 stream 管理 bug。
- aarch64 runner 上构建同一 Dockerfile 是否也失败（当前日志仅含 x86_64 runner 的输出）。
- 24.03-LTS-SP3 的同类镜像（已存在于仓库中）在 CI 重试时是否正常，用于排除仓库全局不可用的可能性。

## 修复验证要求
无需 Code Fixer 介入。此为基础设施故障（HTTP/2 协议错误），须由 CI 运维或仓库运营方排查。
