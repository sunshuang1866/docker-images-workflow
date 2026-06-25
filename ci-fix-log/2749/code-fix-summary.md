# 修复摘要

## 修复的问题
openEuler 24.03-lts-sp3 仓库中的 FreeRDP 被 guacamole-server 1.6.0 的 configure 脚本判定为开发版本，导致构建被拒绝。

## 修改的文件
- `Others/guacd/1.6.0/24.03-lts-sp3/Dockerfile`: 在 `GUACAMOLE_SERVER_OPTS` 中追加 `--enable-allow-freerdp-snapshots` 参数

## 修复逻辑
guacamole-server 的 configure 脚本在检测到 FreeRDP 为开发/快照版本时主动拒绝继续构建，并在错误提示中明确建议使用 `--enable-allow-freerdp-snapshots` 参数绕过检查。该参数是 configure 脚本原生支持的选项，添加后 configure 将跳过 FreeRDP 版本检查，允许正常构建。这是分析报告中置信度最高的修复方向。

## 潜在风险
- `--enable-allow-freerdp-snapshots` 可能允许构建链接到行为不稳定的 FreeRDP 开发版，理论上存在内存泄漏或协议兼容性问题的风险。但这是 configure 官方提供的机制，且同名 guacd 1.6.0 的其他 openEuler 版本（sp1、sp2）也使用相同的 FreeRDP 依赖，构建均成功，说明 openEuler 仓库中的 FreeRDP 包虽被标记为"开发版"但实际可用。