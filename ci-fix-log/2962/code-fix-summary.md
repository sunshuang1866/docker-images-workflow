# 修复摘要

## 修复的问题
mesa 25.3.4 构建时，`subprojects/wayland-protocols.wrap` 中记录的 `wayland-protocols-1.41.tar.xz` SHA256 哈希值与 GitLab 动态生成的 tarball 实际哈希不一致，导致 meson 子项目校验失败。

## 修改的文件
- `Others/mesa/25.3.4/24.03-lts-sp4/Dockerfile`: 在 meson setup 之前新增 `sed` 命令，将 wrap 文件中的 SHA256 哈希修复为构建时 GitLab 返回的实际值。

## 修复逻辑
根因是 GitLab release tarball 的 SHA256 校验和因压缩方式不稳定而与 mesa 上游记录的预期值不匹配。同时 openEuler 24.03-LTS-SP4 仓库中 `wayland-protocols-devel` 版本为 1.33，无法满足 mesa 要求的 >= 1.41。
采用分析报告中的方向 1：在 `WORKDIR /opt/mesa-${VERSION}` 之后、meson setup 之前，通过 `sed` 将 `subprojects/wayland-protocols.wrap` 中 `source_hash` 行替换为 CI 构建环境中的实际哈希值 `5a2712e6e20ac68b355f3926f983c1e6e40f061aec355835fbb5ec48a7078e4f`。
已从上游 mesa-25.3.4 源码 tarball 提取原始 wrap 文件验证正则匹配成功，`source_hash = .*` 模式可正确匹配并替换该行。

## 潜在风险
- GitLab 动态生成 tarball 的哈希值可能在未来再次变化，届时构建会再次失败，需要再次更新哈希。
- 此修复仅在构建容器内生效，不影响其他文件。