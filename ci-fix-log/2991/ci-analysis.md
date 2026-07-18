# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 构建节点: `ecs-build-docker-aarch64-04-sp`（aarch64 架构）
- 失败原因: aarch64 架构构建节点在执行 `dnf install` 从 `repo.openeuler.org` 下载软件包时，多个 RPM 包（git-core、gcc-c++、guile）遭遇 HTTP/2 流层错误（Curl error 92: INTERNAL_ERROR），其中 `guile` 包重试耗尽所有镜像后最终失败，导致整个 `dnf install` 命令以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 此次 PR 仅新增了一个标准的 vvenc Dockerfile（含 `dnf install` + `git clone` + `cmake` 构建流程）和元数据文件更新。Dockerfile 本身在语法和逻辑上没有问题——`dnf install -y git gcc gcc-c++ make cmake` 是合法的包安装命令。失败纯粹是由于 CI 构建期间 `repo.openeuler.org` 镜像站在 aarch64 节点上出现 HTTP/2 协议层传输异常，属于基础设施层面的偶发性网络问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 构建。** 此失败是 `repo.openeuler.org` 软件源在构建时刻的临时性 HTTP/2 流层异常，与 PR 引入的 Dockerfile 内容无任何关联。在 openEuler 镜像站恢复稳定后，重新触发 CI 构建即可通过。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 aarch64 节点上的 HTTP/2 服务是否稳定，是否为临时性抖动
- 检查同一时间段是否有其他 PR 在 aarch64 节点上遇到相同的 `Curl error (92)` 包下载失败，以判断是全局基础设施问题还是该节点独有问题
