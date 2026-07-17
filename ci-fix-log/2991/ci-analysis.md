# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, repo.openeuler.org

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（本次 PR 新增）
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在通过 `dnf install` 从 `repo.openeuler.org` 下载 aarch64 RPM 包时，多个包（`git-core`、`gcc-c++`、`guile`）持续遭遇 HTTP/2 流错误（Curl error 92: `Stream error in the HTTP/2 framing layer: INTERNAL_ERROR`），其中 `guile` 耗尽所有镜像重试次数后彻底失败。`git-core` 在重试后成功下载，但 `gcc-c++` 两次尝试均以相同 HTTP/2 流错误告终，`guile` 最终因 "No more mirrors to try" 失败。

### 与 PR 变更的关联
**与 PR 改动无关**。本 PR 仅新增 vvenc 1.14.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（以及配套的 README、image-info.yml、meta.yml 更新），Dockerfile 内容正确——`dnf install -y git gcc gcc-c++ make cmake` 是标准的构建依赖安装命令。失败根因是 openEuler 官方 aarch64 RPM 仓库（`repo.openeuler.org`）在构建期间 HTTP/2 连接不稳定，属于基础设施层面的网络问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。HTTP/2 流错误（Curl error 92）通常是临时的网络/服务器端问题。该错误影响多个包且发生在 openEuler 官方仓库，非代码缺陷。直接重新触发 CI 构建（无需修改任何代码），有很大概率在仓库恢复稳定后通过。

### 方向 2（置信度: 中）
**在 Dockerfile 中为 dnf 增加重试配置**。若该问题反复出现，可在 `dnf install` 命令中添加 `--setopt=retries=10` 提高 dnf 对单个包的重试次数，或使用 shell 循环对 `dnf install` 整体进行重试（如 `for i in $(seq 1 3); do dnf install ... && break; done`），增加对临时网络波动的容忍度。

### 方向 3（置信度: 低）
**更换 dnf 镜像源**。若 `repo.openeuler.org` 对 aarch64 持续的 HTTP/2 稳定性不佳，可在 Dockerfile 中先用 `sed` 替换 `/etc/yum.repos.d/` 下的 repo 文件，将 baseurl 指向其他镜像站（如华为云镜像 `https://mirrors.huaweicloud.com/openeuler/...`），通过更稳定的镜像源下载 RPM 包。

## 需要进一步确认的点
1. 确认 x86_64 架构的 CI job 是否成功（本日志仅包含 aarch64 构建过程）。如果 x86_64 也失败，则可能与 openEuler 24.03-LTS-SP4 仓库本身的状态有关，而非架构特定问题。
2. 确认 `repo.openeuler.org` 在构建时段是否有已知的服务中断或维护公告。
3. 若问题持续复现，需确认该 CI runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络路径是否存在稳定性的问题（如 HTTP/2 代理中间件问题）。
