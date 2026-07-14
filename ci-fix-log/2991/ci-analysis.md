# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: aarch64 构建环境中，`dnf install` 从 `repo.openeuler.org` 下载 RPM 包（`git-core`、`gcc-c++`、`guile`）时反复出现 HTTP/2 流错误（Curl error 92），其中 `guile` 包耗尽所有镜像重试次数后导致整个 `dnf install` 步骤失败。

### 与 PR 变更的关联
**与 PR 变更无关**。该 PR 仅新增了一个标准的 vvenc Dockerfile 和配套元数据文件。Dockerfile 中的 `dnf install` 命令格式正确，与同仓库中其他 24.03-lts-sp4 镜像的写法一致。失败是 `repo.openeuler.org` 仓库服务器在处理 HTTP/2 请求时出现的瞬时网络层错误（`INTERNAL_ERROR (err 2)`），属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。该错误为 `repo.openeuler.org` 仓库服务器的瞬时 HTTP/2 流错误，属于基础设施层网络波动。多个不同的 RPM 包（`git-core`、`gcc-c++`、`guile`）在下载时均遇到相同的 `Curl error (92)`，排除了特定包损坏的可能性。代码本身无需修改，重新运行 CI 大概率可以成功。

### 方向 2（置信度: 低）
若多次重试仍持续失败，考虑在 `Dockerfile` 的 `dnf install` 命令行或 `/etc/dnf/dnf.conf` 中添加 `--setopt=ip_resolve=4`（强制使用 IPv4），或配置 `retries=10` 提高容错。但此方向仅为缓解手段，根本原因在服务端，不应作为首选方案。

## 需要进一步确认的点
1. 确认 `repo.openeuler.org` 在失败时段是否有服务端异常或维护公告。
2. 确认同一时段其他 PR 的 aarch64 构建是否也出现了相同的 `Curl error (92)`，以确认这是否为系统性事件。
3. 如果重试（如 recheck/retrigger）后仍然失败，需联系 openEuler 镜像站运维排查 HTTP/2 服务器端配置问题。

## 修复验证要求
无需验证。本次失败为 infra-error，PR 代码无缺陷，Code Fixer 无需处理。
