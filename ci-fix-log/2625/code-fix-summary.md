# 修复摘要

## 修复的问题
bind9 9.21.23 构建失败：meson setup 报 `Unknown options: "lmdb"` 错误，因为该版本的 meson 构建系统已移除 `lmdb` 选项。

## 修改的文件
- `Others/bind9/9.21.23/24.03-lts-sp3/Dockerfile`: 从 meson setup 命令中移除 `-Dlmdb=enabled \` 行

## 修复逻辑
已从 bind9 v9.21.23 上游仓库获取 `meson.options` 文件（`https://raw.githubusercontent.com/isc-projects/bind9/v9.21.23/meson.options`）验证，确认 `lmdb` 选项已彻底移除，不存在重命名或替代选项。LMDB 功能在 9.21.23 中已自动检测（由 meson 的 `dependency()` 机制处理），无需显式通过 meson option 开启，因此直接删除 `-Dlmdb=enabled` 即可修复构建错误。`lmdb-devel` 包在 `yum install` 中保留，因为 LMDB 库在自动检测模式下仍需要该开发包。

## 潜在风险
无。其他 meson 选项（gssapi、idn、stats-json、geoip、dnstap）均在上游 `meson.options` 中存在且名称未变，删除仅影响已移除的 `lmdb` 选项。