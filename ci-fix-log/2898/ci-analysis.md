# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 缺少 shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试基础设施（eulerpublisher 的 Check 阶段）依赖 `shunit2` shell 单元测试框架，但当前 aarch64 CI runner 上未安装该工具，导致 `common_funs.sh` 第 13 行 source `shunit2` 时失败，进而 Check 阶段报错退出

### 与 PR 变更的关联
与 PR 变更**无关**。Dockerfile 构建和镜像推送均成功完成（日志中 `[Build] finished` 和 `[Push] finished` 均正常输出，镜像已成功推送到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`）。失败发生在构建完成后的 CI 自身 Check/测试阶段，是 CI 基础设施层面缺少 `shunit2` 依赖所致。

## 修复方向

### 方向 1（置信度: 高）
在 aarch64 CI runner 上安装 `shunit2`。shunit2 是一个 Shell 单元测试框架，通常可通过以下方式之一安装：
- 系统包管理器（如 `yum install shunit2` 或 `dnf install shunit2`）
- 或将 `shunit2` 脚本放置到 `/usr/local/etc/eulerpublisher/tests/container/common/` 目录下使其可被 source

此为 CI 基础设施维护操作，与代码仓库无关，Code Fixer 无需处理。

## 需要进一步确认的点
1. 确认 `shunit2` 在 x86_64 CI runner 上是否已安装（若已安装则说明仅是 aarch64 runner 缺少该依赖）
2. 确认 `shunit2` 应安装到哪个路径（`common_funs.sh` 第 13 行的 source 路径）
3. 确认该 aarch64 runner 上是否其他 PR 的 Check 阶段也因同样原因失败（判断是本次配置还是长期缺失）
