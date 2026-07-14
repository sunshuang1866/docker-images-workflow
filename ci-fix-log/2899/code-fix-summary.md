# 修复摘要

## 修复的问题
guacamole-server 构建时 configure 脚本检测到 FreeRDP 为开发版本而拒绝编译，通过添加 `--enable-allow-freerdp-snapshots` 标志绕过此检查。

## 修改的文件
- `Others/guacd/1.6.0/24.03-lts-sp4/Dockerfile`: 在 `GUACAMOLE_SERVER_OPTS` 中追加 `--enable-allow-freerdp-snapshots`

## 修复逻辑
openEuler 24.03-LTS-SP4 软件源中的 `freerdp`/`freerdp-devel` 包被 guacamole-server 的 configure 脚本判定为开发版本（非稳定发布版），导致构建失败。`--enable-allow-freerdp-snapshots` 是 guacamole-server 官方构建系统提供的内置开关，正是 configure 错误信息中建议的绕过方案。该标志仅解除版本检查限制，不改变编译逻辑或运行时行为，安全且最小化。

## 潜在风险
无。该标志来自 guacamole-server 官方构建系统，仅跳过开发版本检测，不影响编译产物质量。其他已有的 openEuler 版本（如 SP2）如果未遇到此问题，说明其 FreeRDP 包为稳定版本，无需此标志。