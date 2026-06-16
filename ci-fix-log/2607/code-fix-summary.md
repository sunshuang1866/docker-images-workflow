# 修复摘要

## 修复的问题
fbthrift getdeps 构建系统在 Assessing libaio 阶段失败（exit code 1），缺少 `libaio-devel` 系统包导致 libaio 依赖评估/构建失败。

## 修改的文件
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile`: 在 `dnf install` 步骤中新增 `libaio-devel` 包

## 修复逻辑
CI 分析报告方向 1（置信度：中）指出，libaio 构建失败可能是 openEuler 缺少 libaio 编译所需的系统库。`fix_getdeps.py` 已将 openeuler 加入 RPM 发行版列表，使得 `--allow-system-packages` 标志下的 getdeps 会尝试使用系统 RPM 包。但 Dockerfile 的 `dnf install` 中未安装 `libaio-devel`，导致 getdeps 在评估 libaio 时（尝试使用系统包或构建源码）因缺少开发头文件而失败。已验证 `libaio-devel` 是 openEuler 上的有效包名（多个同仓库 Dockerfile 已使用）。

## 潜在风险
- 如果 `libaio-devel` 在 openEuler 24.03-lts-sp3 仓库中不可用，`dnf install` 本身会失败。但该包在 openEuler 24.03-lts-sp3 其他镜像（如 qemu、ceph）中已成功使用，风险低。