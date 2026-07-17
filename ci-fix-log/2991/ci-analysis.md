# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:6（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: openEuler 24.03-LTS-SP4 的 aarch64 RPM 仓库服务器 (`repo.openeuler.org`) 在 HTTP/2 传输层间歇性出现 `INTERNAL_ERROR` 导致流异常关闭，`guile` 包下载耗尽所有重试/镜像后失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 vvenc 的 Dockerfile 和元数据文件，Dockerfile 中的 `dnf install` 命令语法正确。失败发生在 `dnf` 从远程仓库下载 RPM 包阶段，属于 openEuler 官方仓库服务器的 HTTP/2 协议层间歇性故障。日志中可见 `git-core`、`gcc-c++` 等包也遇到了同样的 `Curl error (92)`，但经过重试后成功下载，而 `guile` 包重试耗尽后最终失败。

## 修复方向

### 方向 1（置信度: 中）
**等待 retry / 重新触发 CI。** 此失败属于 `repo.openeuler.org` 仓库服务器的临时性 HTTP/2 协议故障，与 PR 代码无关。重新触发 CI 流水线大概率可以成功（日志中显示此前多个包在同一次构建中也通过重试成功下载了）。无需修改 Dockerfile 或任何代码。

## 需要进一步确认的点
- 如果多次 retry 仍然失败，需排查 `repo.openeuler.org` 的 aarch64 仓库是否存在持续性的 HTTP/2 服务端问题。
- 可单独验证 `https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm` 是否可正常下载。
