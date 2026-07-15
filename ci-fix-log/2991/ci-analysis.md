# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, aarch64, dnf install

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
------
Dockerfile:6
--------------------
   4 |     ARG VERSION=1.14.0
   5 |     
   6 | >>> RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all
   7 |     
   8 |     RUN git clone -b v${VERSION} --depth 1 https://github.com/fraunhoferhhi/vvenc.git && \
--------------------
ERROR: failed to solve: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（新增文件）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `dnf install` 下载依赖包时，`repo.openeuler.org` 镜像站多次返回 HTTP/2 流错误（Curl error 92: Stream error in the HTTP/2 framing layer），其中 `git-core`、`gcc-c++` 各失败 1 次但重试成功，而 `guile` 包在所有 mirror 重试后仍无法下载，导致整个安装步骤失败。这是 openEuler 仓库镜像站的临时网络/协议层故障，与 PR 代码变更无关。

### 与 PR 变更的关联
无关。PR 仅新增了一个标准的 Dockerfile（安装编译依赖 → 克隆源码 → cmake 构建 → 安装），Dockerfile 中的 `dnf install` 命令语法和包名均正确，此前同类 PR（如 24.03-lts-sp3 的 vvenc Dockerfile）使用相同的安装模式均构建成功。失败完全由 CI 构建时 `repo.openeuler.org` 镜像站对 aarch64 架构的 HTTP/2 服务不稳定引起。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 `repo.openeuler.org` 镜像站的临时网络故障（HTTP/2 流在传输 aarch64 RPM 包时被异常关闭）。等待镜像站恢复后触发 CI 重跑即可。若需提高构建成功率，可在 Dockerfile 的 `dnf install` 中添加 `--retries 5` 参数增加重试次数，但这对根本问题无实质改善。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 仓库在 aarch64 架构下的 HTTP/2 镜像服务当前状态是否正常。
- 如重试后仍失败，检查是否为特定 RPM 包（如 `guile-2.2.7-6.oe2403sp4.aarch64.rpm`）在源站确实缺失或损坏（非网络问题），但就当前日志而言，所有错误均为 Curl error 92（HTTP/2 流层错误），指向网络基础设施问题。
