# 修复摘要

## 修复的问题
meson 构建配置阶段因缺少 `wayland-protocols-devel` 包导致 pkg-config 查找失败，触发子项目下载和哈希校验失败，构建终止。

## 修改的文件
- `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`: 在 `dnf install` 命令中添加 `wayland-protocols-devel` 包（第 9 行，紧邻 `wayland-devel` 之后）。

## 修复逻辑
CI 分析报告指出：Dockerfile 已安装 `wayland-devel` 但未安装 `wayland-protocols-devel`，导致 meson 配置时无法通过 pkg-config 发现系统级 wayland-protocols，被迫回落至下载子项目 `wayland-protocols-1.41`，而 mesa 25.3.4 源码内 `subprojects/wayland-protocols.wrap` 记录的 SHA256 哈希值与 GitLab 当前提供的 tar.xz 实际哈希值不匹配，触发 `Incorrect hash for source` 错误。在 `dnf install` 中补充 `wayland-protocols-devel` 可使 meson 通过 pkg-config 直接发现系统已安装的 wayland-protocols，跳过子项目下载路径，从根本上避免哈希校验失败。

关于 `pkgconfig` 拼写：所有现有 mesa Dockerfile（sp1、sp3、sp4）均统一使用 `pkgconfig`，非本 PR 引入的新问题，且与本次 CI 失败无直接关联，不做修改。

## 潜在风险
无。添加 `wayland-protocols-devel` 仅增加一个编译时的 pkg-config 依赖包，不影响运行时行为。若 openEuler 24.03-LTS-SP4 仓库中无此包或版本过低（<1.31），构建仍将失败，但届时可通过方向 2（手动下载匹配版本的 wayland-protocols）解决，不属于本次修复的风险范围。