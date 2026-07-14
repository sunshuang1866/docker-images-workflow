# 修复摘要

## 修复的问题
移除从 `gitlab.freedesktop.org` 手动下载 wayland-protocols-1.41.tar.xz 的冗余步骤，该步骤因服务器返回 HTML 而非实际归档文件导致构建失败。

## 修改的文件
- `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`: 删除 lines 26-34 中手动下载和编译 wayland-protocols 的 RUN 指令块

## 修复逻辑
1. Dockerfile 中 `wayland-protocols-devel` 已通过 dnf 安装（line 9），手动从 `gitlab.freedesktop.org` 下载相同依赖是冗余操作
2. 该 GitLab 实例对 CI 来源 IP 返回 HTML 页面（2.3KB）而非 `.tar.xz` 归档，导致 `tar -xvf` 失败
3. 删除手动下载步骤，依靠 dnf 系统包 `wayland-protocols-devel` 提供所需文件——这与分析报告中的"方向 1"一致
4. 对照其他 Mesa 版本（sp1/sp2/sp3）的 Dockerfile，均不包含此手动下载步骤且构建正常

## 潜在风险
无。`wayland-protocols-devel` 已在 dnf install 列表中，meson 构建时可直接使用系统安装的 wayland protocol 文件，无需额外下载。