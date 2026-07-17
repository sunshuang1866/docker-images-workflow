# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI aarch64 runner 在 `dnf install` 阶段从 `repo.openeuler.org` 下载 RPM 包时，多个大型包（`gcc-c++` 12MB、`git-core` 11MB、`guile` 6.3MB）遭遇 HTTP/2 流错误（Curl error 92），经过多次镜像重试后，`guile` 包耗尽所有镜像仍下载失败，导致 `dnf install` 退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 vvenc 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（及配套的 README、image-info.yml、meta.yml 更新），Dockerfile 中 `dnf install` 命令本身语法正确。失败是由 `repo.openeuler.org` 包仓库在下载大文件时发生的 HTTP/2 协议层传输错误导致的网络基础设施问题。值得注意的是，小包（如 acl 50KB、cmake-filesystem 8KB 等）均下载成功，出错集中在体积较大的 RPM 包上（gcc 30MB、gcc-c++ 12MB、git-core 11MB、guile 6.3MB），其中 `git-core` 在重试后成功，`gcc-c++` 第二次重试仍失败但未致命，最终 `guile` 耗尽所有镜像而致命失败。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 这是一个临时性网络基础设施问题（`repo.openeuler.org` CDN/镜像节点的 HTTP/2 连接在下载大文件时偶发中断）。无需修改任何代码，在 `repo.openeuler.org` 网络状况恢复后重新触发 CI 构建即可通过。

### 方向 2（置信度: 低）
如果该问题反复出现（在同一 CI runner 上频繁发生），可在 Dockerfile 的 `dnf install` 命令前添加网络容错措施，或向 openEuler 基础设施团队反馈 `repo.openeuler.org` 的 aarch64 仓库节点 HTTP/2 链路稳定性问题。

## 需要进一步确认的点
- 同一 PR 的 x86_64 架构构建是否成功（当前日志仅包含 aarch64 runner 的输出）。
- `repo.openeuler.org` 在 CI 失败时段是否存在已知的服务降级或网络抖动。
- 该 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络路径是否稳定（可用 `mtr` 或 `traceroute` 排查）。
