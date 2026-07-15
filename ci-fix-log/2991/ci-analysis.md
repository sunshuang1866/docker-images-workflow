# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 系统仓库下载流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install

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
- 失败原因: CI 在 aarch64 runner 上构建镜像时，`dnf install` 从 `repo.openeuler.org` 下载 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 等 RPM 包过程中，openEuler 24.03-LTS-SP4 仓库服务器返回 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），同一包多次重试均失败，最终 `guile` 包耗尽所有镜像源后安装失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 内容完全正确——它只是在 openEuler 24.03-lts-sp4 基础镜像上通过 `dnf install` 安装必要的编译工具（git、gcc、gcc-c++、make、cmake），然后编译安装 vvenc 1.14.0。失败发生在 `dnf install` 从 openEuler 官方仓库下载依赖包阶段，属于 CI 基础设施/网络层面的问题。日志显示多个 RPM 包（`git-core`、`gcc-c++`、`guile`）均遭遇了 HTTP/2 流错误，其中 `guile` 最终无法下载导致构建失败。

## 修复方向

### 方向 1（置信度: 高）
**重试触发 CI 重新构建。** 该失败为 openEuler 24.03-LTS-SP4 官方仓库在构建期间的临时性 HTTP/2 服务端问题，与 PR 代码无关。等待仓库服务恢复后，重新触发 CI 流水线大概率可以通过。无需修改任何代码。

### 方向 2（置信度: 中）
如重试多次持续失败，可考虑在 Dockerfile 的 `dnf install` 命令前添加 `dnf makecache --refresh` 或配置更稳健的镜像源（如华为云镜像 `repo.huaweicloud.com`）替代 `repo.openeuler.org`，但此操作仅作为绕过基础设施问题的临时手段，不推荐作为常规修复。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库（`repo.openeuler.org`）在构建时段是否存在已知的服务端 HTTP/2 问题或维护窗口。
- 其他同样使用 openEuler 24.03-lts-sp4 基础镜像的 PR 是否在相近时段也出现同类 `Curl error (92)` 失败（可据此确认是否为仓库侧系统性问题）。
