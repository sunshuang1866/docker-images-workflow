# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, aarch64, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: aarch64 架构构建时，`dnf install` 从 `repo.openeuler.org` 下载多个 aarch64 RPM 包时遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），`git-core` 和 `gcc-c++` 经 dnf 自动重试后成功，但 `guile-5:2.2.7-6.oe2403sp4.aarch64` 重试耗尽后下载失败，导致整个 `dnf install` 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`）语法和内容均正确，与已有 SP3 版本的 Dockerfile 构建逻辑一致。失败完全由 openEuler 24.03-LTS-SP4 的 aarch64 软件仓库 HTTP/2 传输层稳定性问题引起，属于 CI 基础设施层面的网络故障。PR 的 README.md、image-info.yml、meta.yml 等元数据变更均为标准格式，不涉及构建逻辑。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败为 transient infra-error（瞬时网络故障），HTTP/2 流错误通常由服务端或中间网络设备临时不稳定引起，重试后大概率可成功。Code Fixer 无需修改任何代码。

## 需要进一步确认的点
- 若重试后 aarch64 构建仍持续失败，需确认 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 仓库是否存在 HTTP/2 协议配置问题或持续性的网络故障。
- 可尝试在 Dockerfile 中为 dnf 添加下载重试参数（如 `--setopt=retries=10`）或改用 HTTP/1.1 降级 curl 协议，但这些属于迁就性 workaround，非根因修复。
