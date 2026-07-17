# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, aarch64

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
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库 `repo.openeuler.org` 在向 aarch64 runner 提供 RPM 包下载时，HTTP/2 流层面持续出现 `INTERNAL_ERROR (err 2)`，导致 `git-core`、`gcc-c++`、`guile` 三个包下载失败。其中 `guile` 包在重试耗尽后最终致命失败。这是在 Docker 镜像构建的第一步 `dnf install` 阶段发生的网络基础设施问题。

### 与 PR 变更的关联
**与 PR 无关。** PR 的变更仅为新增 vvenc 1.14.0 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 本身语法和内容正确。失败发生在 `dnf install -y git gcc gcc-c++ make cmake` 这个标准依赖安装步骤，根因是 `repo.openeuler.org` 仓库服务的 HTTP/2 协议层问题（`Stream error in the HTTP/2 framing layer`，`INTERNAL_ERROR (err 2)`），属于 CI 基础设施侧的 transient network failure。Code Fixer 无需处理。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是一个 `infra-error`——CI 构建环境中 `repo.openeuler.org` 的 aarch64 仓库在 HTTP/2 协议层出现问题，属于仓库服务器端的瞬时故障。建议直接重新触发 CI 运行（re-run/retry），等待仓库服务恢复正常后构建即可通过。

### 方向 2（可选，置信度: 中）
如果重试多次仍然失败，可考虑在 Dockerfile 的 `dnf install` 命令前添加对 openEuler 仓库的降级措施，例如强制 dnf 使用 HTTP/1.1 而非 HTTP/2（在 dnf 配置中设置 `http2=false` 或通过 curl 层面的环境变量降级），以绕过 HTTP/2 流错误。但这属于绕过基础设施问题的 workaround，不应作为首选方案。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 aarch64 仓库 HTTP/2 服务状态是否已恢复正常（可通过浏览器或 curl 直接访问对应 RPM URL 验证）
- 如果反复出现同类 HTTP/2 stream error，需联系 openEuler 基础设施团队排查仓库服务器的 HTTP/2 配置
- 确认同一时间段内其他 openEuler 24.03-LTS-SP4 镜像的 CI 构建是否也遇到了相同的 HTTP/2 错误（以判断是偶发还是系统性故障）
