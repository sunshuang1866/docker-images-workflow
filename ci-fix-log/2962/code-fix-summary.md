# 修复摘要

## 修复的问题
CI 构建失败：meson setup 解包 wayland-protocols 子项目时，缓存的 `wayland-protocols-1.41.tar.xz` 为无效文件（非压缩 tar 格式），导致构建失败。

## 修改的文件
- `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`: 移除手动 wget 下载 wayland-protocols 的步骤（原第26-31行）及 dnf 中的 `wayland-protocols-devel` 包（原第9行），使构建配置与已验证可用的 SP3 版本一致。

## 修复逻辑
1. **根因**：Dockerfile 中通过 `wget -q` 从 GitLab 下载 wayland-protocols-1.41.tar.xz 并预填充到 meson 的 `subprojects/packagecache/`。GitLab 的 Anubis 防护机制向 CI runner 返回 HTML 挑战页面（而非实际 tar.xz 文件），而 `wget -q` 静默模式掩盖了下载错误，导致 HTML 被错误保存为 .tar.xz 文件。随后 meson setup 尝试解包时报告 "not a compressed or uncompressed tar file"。

2. **修复方案**：参考同目录下已验证可用的 `25.3.4/24.03-lts-sp3/Dockerfile`，该文件不使用手动 wget 下载步骤，依赖 meson 内置的 subproject wrap 机制自动处理 wayland-protocols 的下载。meson 内部使用 Python urllib 进行下载，可能使用不同的传输层，避免或缓解了 Anubis 拦截问题。

3. **改动内容**：
   - 从 dnf install 列表中移除 `wayland-protocols-devel`（SP3 中亦未安装此包，且其版本 1.33 不满足 mesa 25.3.4 的 >= 1.41 要求，安装后反而触发版本检查导致不必要的回退逻辑）
   - 移除整个手动 wget 下载及 packagecache 预填充步骤（共6行）
   - meson 在找不到系统 wayland-protocols 后会自然回退到 subproject wrap 机制自行下载 1.41 版本

## 潜在风险
- 如果 meson 内置下载机制同样被 GitLab Anubis 拦截，构建仍可能失败。但 SP3 版本的 Dockerfile（无此下载步骤）已验证可成功构建，降低了此风险。
- 移除 `wayland-protocols-devel` 后，若构建过程中其他环节依赖该包提供的 XML 协议文件，可能引发新问题。但 SP3 验证显示此依赖不存在。