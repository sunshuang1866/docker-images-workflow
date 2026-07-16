# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, aarch64, dnf install, No more mirrors to try

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
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，`dnf install` 从 `repo.openeuler.org` 下载 RPM 包过程中多次遭遇 HTTP/2 流错误（Curl error 92: `INTERNAL_ERROR`），导致 `git-core`、`gcc-c++` 等包下载重试，最终 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 耗尽所有镜像源仍下载失败，`dnf install` 以退出码 1 失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile` 及配套的 README、image-info.yml、meta.yml 元数据更新。Dockerfile 内容正确，无语法错误、路径错误或版本引用错误。所有变更均为常规的新镜像添加操作。失败完全由 `repo.openeuler.org` 镜像站的 aarch64 仓库 HTTP/2 传输层异常导致，属于 CI 基础设施层面的网络问题。

## 修复方向

### 方向 1（置信度: 中）
**等待 `repo.openeuler.org` 服务器端恢复后重试。** 多次 HTTP/2 stream INTERNAL_ERROR 提示镜像站服务器侧 HTTP/2 协议栈存在临时性故障。若服务器在短时间内恢复，重新触发 CI 即可通过。无代码修改需要。

### 方向 2（置信度: 低）
**若问题持续复现，联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 aarch64 仓库 HTTP/2 配置。** 适用于错误在多日多次重试后仍无法消除的场景，此时需排查是否是镜像站 HTTP/2 服务端配置或 CDN 节点问题。此方向不涉及 PR 代码变更。

## 需要进一步确认的点
1. 在 x86_64 架构 runner 上同 PR 构建是否通过（日志仅覆盖 aarch64 runner）。
2. `repo.openeuler.org` 镜像站的状态监控或公告中是否有已知的服务中断记录。
3. 同一时段内其他 PR 的 aarch64 构建是否也触发了相同错误（用于确认是单例还是服务端系统性故障）。

## 修复验证要求
（无需填写——此失败为 infra-error，不涉及代码修复。）
