# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf仓库HTTP/2流中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 yum/dnf 仓库镜像服务器在处理 HTTP/2 连接时出现瞬态流中断（Curl error 92: INTERNAL_ERROR），多个 RPM 包（gcc-gfortran、guile、gcc）的下载被中断。重试机制耗尽所有可用镜像后，`gcc` 包下载最终失败，导致 `dnf install` 返回 exit code 1。同一构建任务中的另一个并行 stage（#7，安装 gcc-gfortran、make、openblas-devel、lapack-devel）也出现了同类 Curl error 92（针对 glibc-devel 和 gcc-gfortran），但因包数量较少、重试成功而未被波及，#7 因 #8 失败被 CANCEL。

### 与 PR 变更的关联
**与 PR 无关。** PR 变更仅包含：
- 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（47 行，标准的多阶段构建 Dockerfile）
- 更新 `Others/multiwfn/meta.yml`（新增 `cb37c53-oe2403sp4` 条目）
- 更新 `Others/multiwfn/README.md` 和 `Others/multiwfn/doc/image-info.yml`（文档条目）

Dockerfile 中的 `dnf install` 命令语法正确、包名列表与其他架构已有的 `cb37c53-oe2403sp3` 版本一致。失败发生在 dnf 从 openEuler 官方仓库（`repo.****.org`）下载 RPM 包阶段，属于外部仓库服务器的 HTTP/2 连接中断，与 PR 的任何代码变更无关。Code Fixer 无需处理。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 此失败属于 CI 基础设施问题——openEuler 24.03-LTS-SP4 仓库镜像服务器的 HTTP/2 层出现了瞬态错误。建议直接重新触发 CI 构建（retry），大概率可以成功通过。如果多轮重试均无法通过，则需要通知基础设施团队排查 openEuler 仓库镜像的 HTTP/2 服务端配置或网络层问题。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 的 `repo.****.org`（被脱敏的仓库域名）近期是否存在 HTTP/2 服务不稳定或维护窗口。
- 同一时段内其他依赖 `openEuler:24.03-lts-sp4` 基础镜像的 PR 构建是否也出现了相同的 Curl error 92（以确认是全局性问题还是间歇性问题）。
