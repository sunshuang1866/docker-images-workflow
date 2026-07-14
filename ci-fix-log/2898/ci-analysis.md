# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 主机上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试编排工具 `eulerpublisher` 在 [Check] 阶段执行镜像验证测试时，`common_funs.sh` 尝试 source `shunit2`（Bash 单元测试框架），但该框架未安装在 CI runner 上，导致测试脚本执行失败。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建和推送均已成功完成：
- 步骤 #7: Go 源码下载解压 → DONE 67.8s
- 步骤 #8: 文件时间戳与符号链接 → DONE 40.5s
- 步骤 #9: 卸载构建依赖 → DONE 1.5s
- 步骤 #11: 镜像导出推送 → DONE 41.9s（`openeulertest/go:1.25.6-oe2403sp4-aarch64`）

失败仅发生在 eulerpublisher 的后置 [Check] 阶段。PR 变更仅新增 Dockerfile 和元数据文件，无法导致 CI 主机上 `shunit2` 测试框架缺失。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 主机上安装 `shunit2` Bash 测试框架。以 RHEL/openEuler 系系统为例：
```bash
dnf install shunit2 -y
```
或在 CI 编排脚本中确保 `shunit2` 已预装（添加至 CI runner 的初始化/配置脚本 `eulerpublisher` 的环境依赖声明）。

### 方向 2（置信度: 低，备选）
若 `shunit2` 无法通过系统包管理器安装，可从 GitHub 下载 `shunit2` 脚本并放置到 CI runner 的 `PATH` 可搜索路径中（如 `/usr/local/bin/`），使 `common_funs.sh` 能正常 source 到。

## 需要进一步确认的点
- 确认 CI runner 上是否已有其他架构/版本的 runner 安装了 `shunit2`（若 `x86_64` 的 CI runner 有 `shunit2` 而 aarch64 runner 没有，说明是 aarch64 runner 初始化遗漏）。
- 确认 eulerpublisher 的依赖声明中是否列出了 `shunit2`，若未列出则应补充至安装脚本。
- 同 PR 中加入的 x86_64 构建 job 的日志是否也因同样问题失败（本次仅提供了 aarch64 日志），若 x86_64 也失败，则问题覆盖面更广。
