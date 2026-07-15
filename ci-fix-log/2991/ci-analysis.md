# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, dnf install

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: `repo.openeuler.org` 开放欧拉 24.03-LTS-SP4 的 aarch64 软件源存在 HTTP/2 协议层故障，多个 RPM 包（`git-core`、`gcc-c++`、`guile`）在下载过程中遭遇 `Stream error in the HTTP/2 framing layer: INTERNAL_ERROR (err 2)`。其中 `git-core` 和 `gcc-c++` 经多次重试后成功，但 `guile` 耗尽所有镜像重试次数后最终失败，导致 `dnf install` 以 exit code 1 退出。

### 与 PR 变更的关联
**无关。** PR 的改动仅为新增 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile` 及其配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 本身的 `RUN dnf install` 语法完全正确，失败原因是 openEuler 官方软件源服务器端 HTTP/2 通信异常，与 PR 代码变更无关。同一时间内，任何依赖 `dnf install` 从 24.03-LTS-SP4 aarch64 源下载包的构建都可能遇到相同问题。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。该错误为 `repo.openeuler.org` 服务器端临时的 HTTP/2 协议故障，属于 CI 基础设施问题。等待软件源服务恢复后重新触发 CI 构建即可通过。若持续失败，可考虑在 Dockerfile 中 `dnf install` 前增加重试逻辑或更换镜像源。

### 方向 2（置信度: 低）
**更换软件源镜像**。若 `repo.openeuler.org` 的 HTTP/2 问题持续存在，可将 dnf 仓库源临时切换为其他可用的 openEuler 镜像站点（如华为云镜像站），但此类修改涉及基础环境的变更，不应作为常规修复手段。

## 需要进一步确认的点
1. `repo.openeuler.org` 的 aarch64 软件源 HTTP/2 服务当前是否已恢复正常——可通过重新触发 CI 构建（rerequest review / 关闭重开 PR）验证。
2. 是否仅有 CSP4 的 aarch64 源存在此问题，还是影响到所有架构——需确认同期其他 PR 在 x86_64 和 aarch64 上的构建状态。
3. `guile` 包是否是该构建中唯一因耗尽重试次数而失败的包，还是日志截断导致遗漏了其他失败包——日志中 `gcc-c++` 也出现两次 HTTP/2 错误但未显示最终状态，需完整日志确认 `gcc-c++` 是否也下载失败。

## 修复验证要求
无需代码修复。若需通过更换镜像源方式绕过此问题，code-fixer 应：
1. 确认替换后的镜像源确实包含 openEuler 24.03-LTS-SP4 aarch64 仓库的全部所需 RPM 包。
2. 重新触发 CI 构建验证 `dnf install` 步骤完整通过。
