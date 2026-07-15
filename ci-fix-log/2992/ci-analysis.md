# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像在 HTTP/2 传输层出现流错误（Curl error 92: HTTP/2 stream not closed cleanly: INTERNAL_ERROR），导致多个 RPM 包（gcc、gcc-gfortran、guile、glibc-devel）下载失败，`dnf` 在所有镜像均已尝试后放弃，构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 新增了一个合法的 Dockerfile（结构正确，包名均为 openEuler 24.03-LTS-SP4 仓库中存在的标准包），以及 README、image-info.yml、meta.yml 的配套更新。构建失败纯粹由 openEuler 24.03-LTS-SP4 软件仓库镜像的 HTTP/2 服务器端问题引起——包括 builder 阶段（#8）和 final 阶段（#7）在内的两个并行 `dnf install` 进程均遭遇了不同程度的 HTTP/2 流中断，且因镜像重试耗尽而最终失败。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重新触发 CI 构建即可。** 该失败是 openEuler 24.03-LTS-SP4 软件仓库镜像服务器的瞬时 HTTP/2 网络故障，与 PR 代码变更完全无关。待仓库服务器恢复后重试 CI 即可通过。

### 方向 2（置信度: 低）
若该仓库镜像持续返回 HTTP/2 流错误，可在 Dockerfile 中在 `dnf install` 之前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制 dnf 回退到 HTTP/1.1 协议，绕过 HTTP/2 层面的问题。但此为临时规避手段，不推荐作为持久方案。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 软件仓库镜像 `repo.****.org` 的 HTTP/2 服务健康状况——这需要运维侧排查，not code-fixer 范围。
- 同一时间点其他 openEuler 24.03-LTS-SP4 镜像的 CI 构建是否也出现相同错误——若大量失败则确认是仓库侧问题。
