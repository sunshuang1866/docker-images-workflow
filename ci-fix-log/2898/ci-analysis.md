# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Build] finished
2026-07-09 12:32:51,073 - INFO - [Push] finished
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 的 `[Check]` 测试阶段（`eulerpublisher` 工具链），非 Dockerfile 或源码
- 失败原因: CI 测试环境的 `shunit2` shell 测试框架未安装或不在 `PATH` 中，`common_funs.sh` 第 13 行尝试 source `shunit2` 时失败

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建（步骤 #7-#10）和推送（步骤 #11）均成功完成：
- 构建阶段：Go 1.25.6 下载、解压、文件时间戳设置、符号链接创建均正常完成（步骤 #7 DONE 67.8s, #8 DONE 40.5s）
- 清理阶段：构建依赖（gcc、glibc-devel 等）移除成功（步骤 #9 DONE 1.5s）
- 推送阶段：镜像清单和层推送到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64` 成功（`#11 DONE 41.9s`）

失败仅发生在镜像构建和推送全部完成之后的 `[Check]` 测试执行阶段，是 CI 基础设施的测试工具缺失问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` 测试框架（如 `dnf install shunit2`），确保测试脚本 `common_funs.sh` 能正确 source 该库。

### 方向 2（置信度: 中）
如果 `shunit2` 确实已安装但路径不在测试脚本的搜索范围内，需调整 `common_funs.sh` 中的 source 路径或 CI 环境的 `PATH`。

## 需要进一步确认的点
- CI 测试环境（`ecs-build-docker-aarch64-01-sp` runner）上是否未预装 `shunit2`，或 `shunit2` 包名在 openEuler 仓库中是否不同（如 `shunit2` vs `shunit`）
- 该 runner 上同类型其他镜像（如 go 1.25.6-oe2403sp3）的 `[Check]` 阶段是否也同样因 `shunit2` 缺失而失败——如果是，说明是 runner 环境整体退化，与本次 PR 无关
