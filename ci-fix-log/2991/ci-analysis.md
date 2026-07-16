# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: "仓库HTTP/2流错误"
- 新模式症状关键词: "Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, No more mirrors to try, dnf install"

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `dnf install -y git gcc gcc-c++ make cmake` 时，`repo.openeuler.org` 仓库服务器对多个 RPM 包（`git-core`、`gcc-c++`、`guile`）的 HTTP/2 下载响应出现 `INTERNAL_ERROR`（curl error 92），其中 `guile` 包在所有镜像重试后仍失败，导致 dnf 安装整体失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 `vvenc` 镜像的 Dockerfile 及相关元数据文件（README、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 命令内容正确、格式规范。失败纯粹是 openEuler 24.03-LTS-SP4 的 aarch64 软件仓库在构建时段出现 HTTP/2 协议层面的网络不稳定所致——多次下载中断（stream 39、43、49、51 均报 INTERNAL_ERROR），属于 CI 基础设施/上游仓库侧的网络问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 该失败为上游软件仓库 `repo.openeuler.org` 的 aarch64 节点在构建时段的网络波动引起的间歇性 infra-error。建议直接 **retry CI**（重跑失败的 job），待仓库网络恢复后应可通过。

### 方向 2（置信度: 中）
如果重试多次后依然失败，说明 `repo.openeuler.org` 的 aarch64 节点对特定包（如 `guile`）的 HTTP/2 服务可能存在持续性问题。可在 Dockerfile 的 dnf 命令前添加 `--setopt=retries=10` 增加重试次数，或为 dnf 配置 HTTP/1.1 回退（`echo "http2=false" >> /etc/dnf/dnf.conf`），以规避 HTTP/2 流错误。但优先建议先重试确认是否为偶发网络问题。

## 需要进一步确认的点
- 若重试后仍然失败，需确认 openEuler 24.03-LTS-SP4 aarch64 仓库对 `guile` 等包的 HTTP/2 服务是否存在持续性问题。
- 建议在 openEuler 基础设施侧排查 `repo.openeuler.org` 的 aarch64 节点 HTTP/2 流稳定性。
