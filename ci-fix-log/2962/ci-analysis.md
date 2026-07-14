# CI 失败分析报告

## 基本信息
- PR: #2962 — chore(mesa): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式32（同类症状，不同主机）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#12 0.063 --2026-07-14 20:04:47--  https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz
#12 0.472 HTTP request sent, awaiting response... 200
#12 1.024 Length: unspecified [text/html]
#12 1.024 Saving to: 'wayland-protocols-1.41.tar.xz'
#12 1.024      0K ..                                                     78.6M=0s
#12 1.024 2026-07-14 20:04:48 (78.6 MB/s) - 'wayland-protocols-1.41.tar.xz' saved [2390]
#12 1.027 xz: (stdin): File format not recognized
#12 1.027 tar: Child returned status 1
#12 1.027 tar: Error is not recoverable: exiting now
#12 ERROR: process "/bin/sh -c cd /opt && wget https://gitlab.freedesktop.org/wayland/wayland-protocols/-/releases/1.41/downloads/wayland-protocols-1.41.tar.xz && tar -xvf wayland-protocols-1.41.tar.xz ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: Dockerfile:26（CI 构建上下文中的 Dockerfile，含 wayland-protocols 下载步骤，非 PR 提交的原始 Dockerfile）
- 失败原因: 从 `gitlab.freedesktop.org` 下载 `wayland-protocols-1.41.tar.xz` 时，服务器返回了 HTML 页面（2390 字节）而非实际的 `.tar.xz` 归档文件，`tar` 无法识别文件格式导致解压失败。这与 **模式32 (Git快照返回HTML)** 高度相似——服务器抗爬/反机器人机制返回 HTML 代替实际二进制文件。

### 与 PR 变更的关联
- PR 提交的 Dockerfile **本身不包含** wayland-protocols 下载步骤。提交的 Dockerfile（56 行）直接从 pip install 进入 meson build。
- CI 日志显示的 `Dockerfile:26` 含 wayland-protocols 下载，与 PR 中 Dockerfile 的行号/内容不匹配，说明 CI 管道有预处理步骤，检测到 meson 参数 `-Dplatforms=x11,wayland` 后自动注入了 wayland-protocols 源码下载步骤。
- 失败的直接原因是 CI 注入的下载源 `gitlab.freedesktop.org` 不可靠，与 PR 提交的 Mesa 构建逻辑本身无关。

## 修复方向

### 方向 1（置信度: 高）
将 wayland-protocols 的获取方式从直接下载 `gitlab.freedesktop.org` 的 release 归档，改为通过 openEuler 系统包管理器安装。`wayland-devel` 已在 dnf install 列表中，可补充 `wayland-protocols-devel`（或 openEuler 仓库中对应的包名），避免依赖外部网络下载。

### 方向 2（置信度: 中）
如果 openEuler 24.03-LTS-SP4 仓库中没有 `wayland-protocols-devel` 包，则将 wayland-protocols 下载源从 `gitlab.freedesktop.org`（GitLab 实例）更换为其他可靠镜像或官方 GitHub release（`https://gitlab.freedesktop.org/wayland/wayland-protocols` 的 mirror 或 `https://github.com/wayland-project/wayland-protocols` 等）。

### 方向 3（置信度: 低）
尝试通过 CI 管道的预处理配置层面解决问题——将 wayland-protocols 下载步骤从 CI 自动注入逻辑中排除，改为在 PR 的 Dockerfile 中显式、可控地管理该依赖。

## 需要进一步确认的点
1. CI 的 wayland-protocols 注入逻辑位于何处（预处理脚本/job 模板）？需要确认是哪个组件负责在检测到 `-Dplatforms=wayland` 时注入下载步骤，以便定位修改点。
2. openEuler 24.03-LTS-SP4 仓库中是否存在 `wayland-protocols-devel` 或等效包？若存在，可直接通过 dnf 安装，彻底消除外部网络下载依赖。
3. `gitlab.freedesktop.org` 是否对 CI 来源 IP 有访问限制？需要确认该 GitLab 实例的下载链路是否因 IP/UA 策略被拦截。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。
