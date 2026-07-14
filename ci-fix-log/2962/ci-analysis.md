# CI 失败分析报告

## 基本信息
- PR: #2962 — chore(mesa): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: GitLab 发布页面返回 HTML
- 新模式症状关键词: text/html, File format not recognized, gitlab.freedesktop.org, wayland-protocols, tar, xz

## 根因分析

### 直接错误
```
#12 [7/8] RUN wget -O /tmp/wayland-protocols-1.41.tar.xz https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz     && tar -xvf /tmp/wayland-protocols-1.41.tar.xz -C /tmp     && cd /tmp/wayland-protocols-1.41     && meson setup build     && meson install -C build     && rm -rf /tmp/wayland-protocols-1.41 /tmp/wayland-protocols-1.41.tar.xz
#12 0.855 Length: unspecified [text/html]
#12 0.855 Saving to: '/tmp/wayland-protocols-1.41.tar.xz'
#12 0.855      0K ..                                                     68.0M=0s
#12 0.855 2026-07-14 20:53:14 (68.0 MB/s) - '/tmp/wayland-protocols-1.41.tar.xz' saved [2390]
#12 0.857 xz: (stdin): File format not recognized
#12 0.857 tar: Child returned status 1
#12 0.857 tar: Error is not recoverable: exiting now
#12 ERROR: process "/bin/sh -c wget -O /tmp/wayland-protocols-1.41.tar.xz ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: Docker 构建的步骤 #12（[7/8]，由 CI 注入的 wayland-protocols 依赖安装步骤）
- 失败原因: `wget` 请求 `gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz` 时，服务器返回了 HTML 页面（仅 2390 字节，Content-Type 为 `text/html`），而非实际的 `.tar.xz` 压缩包。`tar -xvf` 无法识别 HTML 文件格式，报 `File format not recognized` 后退出。

### 与 PR 变更的关联
**与 PR 改动无直接关联。** PR #2962 新增的 Dockerfile（`Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`）仅有 56 行，包含 dnf 安装依赖、下载 mesa 源码、pip 安装 meson 以及 `meson setup/compile/install` 步骤，**不包含** wayland-protocols 的下载与构建步骤。该步骤（Dockerfile:26 处的 `RUN wget ... wayland-protocols-1.41.tar.xz`）是由 CI 构建管道/builder 模板注入的——因为 mesa 的构建配置中指定了 `-Dplatforms=x11,wayland`，CI 系统自动添加了 wayland-protocols 作为前置依赖。

实际失败原因是 `gitlab.freedesktop.org` 对该 release 下载 URL 返回了 HTML 页面（可能为重定向页、登录页或格式已变更的页面），而非原始压缩包。此问题同样会影响其他需要 wayland-protocols 作为依赖的镜像构建。

## 修复方向

### 方向 1（置信度: 高）
wayland-protocols 的 GitLab release 下载 URL 返回了 HTML 而非 tarball。可能的原因：
- GitLab 的 release asset 下载 URL 格式已变更（如路径或参数不同）
- 该 release 的实际 asset 文件名与 URL 中构造的文件名不一致
- GitLab 实例现在要求认证或已启用防爬机制

修复思路：将 wayland-protocols 的下载源从 `gitlab.freedesktop.org` 的 release 页面下载链接，切换为可直达的源码归档镜像（如 `https://gitlab.freedesktop.org/wayland/wayland-protocols/-/archive/1.41/wayland-protocols-1.41.tar.gz` 使用 GitLab 的 archive API，或从其他镜像站获取）。需确认目标 URL 确实返回有效的 tar 压缩包。

### 方向 2（置信度: 中）
如果 `gitlab.freedesktop.org` 的 archive API 同样返回 HTML，则可考虑从其他可靠源获取 wayland-protocols（如 `github.com/wayland-project/wayland-protocols` 的 GitHub mirror 或直接从 `wayland.freedesktop.org` 下载）。优先验证是否存在 GitHub mirror 提供该版本的发布制品。

## 需要进一步确认的点
1. 该 wayland-protocols 下载步骤是在哪个 CI 模板/builder 脚本中注入的？需要定位对应模板文件以修改 URL。
2. 确认 `gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41` 页面上实际可下载的 asset 文件名是什么（可能与 URL 中构造的 `wayland-protocols-1.41.tar.xz` 不同）。
3. 验证替代下载源（如 GitLab archive API `/-/archive/1.41/wayland-protocols-1.41.tar.gz`）是否可用且返回有效的 tar 包。
4. 检查其他已有的 SP3 或更早版本的 mesa/wayland 相关镜像构建是否也受到相同影响，以判断这是新发问题还是已长期存在的问题。

## 修复验证要求
若修复方向涉及更换 wayland-protocols 的下载 URL：
- code-fixer 必须在实际 CI 环境中执行 `wget` 测试，验证新 URL 返回的文件确实是有效的 tar 压缩包（文件大小至少数百 KB，`file` 命令输出为 `XZ compressed data` 或 `gzip compressed data`），而非 HTML 页面。
- 修复后需触发完整构建（包括 x86_64 和 aarch64），确认 wayland-protocols 安装步骤通过且后续的 mesa meson 构建能正常进行。
