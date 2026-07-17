# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像服务器在 HTTP/2 协议层面持续返回 `INTERNAL_ERROR (err 2)`，导致 curl 下载多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）失败，经过全部镜像重试后 dnf 无法完成软件包安装，Docker 构建在 builder 阶段的 `dnf install` 步骤崩溃。该错误与 PR 代码变更完全无关，属于仓库镜像基础设施问题。

### 与 PR 变更的关联
PR 变更仅新增了一个新 OS 版本（24.03-lts-sp4）的 Dockerfile 及配套元数据/文档更新，Dockerfile 内容（软件包列表、构建步骤）与已有的 `24.03-lts-sp3` Dockerfile 结构一致，无语法错误或逻辑缺陷。失败原因是 CI 构建环境中 openEuler 24.03-LTS-SP4 仓库镜像在本次构建时发生 HTTP/2 服务端错误，与 PR 改动无关。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题（RPM 仓库镜像 HTTP/2 协议异常），非代码缺陷，无需修改 Dockerfile 或任何 PR 文件。等待仓库镜像服务恢复后重新触发 CI 构建即可。如果问题持续出现，可考虑在 Dockerfile 的 `dnf install` 命令前添加 `dnf makecache --refresh` 或调整 DNF 的 HTTP/2 回退配置（如强制使用 HTTP/1.1），但此类调整属于治标手段，根本解决需修复仓库端 HTTP/2 服务问题。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库镜像 `repo.****.org` 在 CI 运行时段是否存在已知的 HTTP/2 服务中断或降级事件。
- 同一仓库镜像在同一时段是否影响了其他 openEuler 24.03-lts-sp4 相关的 PR 构建（可通过查看近期的同版本 PR CI 状态交叉验证）。
- 重试 CI 后问题是否复现，若复现则需联系仓库运维排查 HTTP/2 代理/负载均衡器配置。
