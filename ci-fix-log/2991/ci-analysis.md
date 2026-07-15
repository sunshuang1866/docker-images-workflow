# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, repo.openeuler.org

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `dnf install` 时，`repo.openeuler.org` 仓库镜像在 HTTP/2 传输层出现流错误（`INTERNAL_ERROR`），导致多个 RPM 包（git-core、gcc-c++、guile）下载失败，最终因 `guile-2.2.7-6` 重试耗尽而终止构建。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增一个标准格式的 Dockerfile（`dnf install` 安装 git/gcc/gcc-c++/make/cmake），以及配套的 README、image-info.yml、meta.yml 元数据更新。Dockerfile 的 `dnf install` 命令本身语法正确，失败完全由 `repo.openeuler.org` 仓库在构建时刻的 HTTP/2 协议不稳定导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 该失败为临时性基础设施问题——`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 仓库在 aarch64 构建节点上发生了 HTTP/2 传输层错误。建议触发 CI 重新运行（re-run），若仓库服务恢复正常，构建应当能通过。

### 方向 2（置信度: 低）
如果该仓库镜像持续不可用，可考虑在 Dockerfile 的 `dnf install` 命令前添加 `echo` 配置替换为备用镜像源（如华为云 `repo.huaweicloud.com`），但当前日志中 git-core 重试后成功下载（1513.9），说明为间歇性故障，更换镜像源的必要性较低。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库当前 HTTP/2 服务状态是否已恢复。
- 确认同一时间段内其他 PR 的 aarch64 构建是否也出现相同的 Curl error (92)（如存在，进一步确认为基础设施侧问题）。
