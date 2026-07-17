# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`（CI runner 上的测试框架脚本）
- 失败原因: CI 测试框架脚本 `common_funs.sh` 在第 13 行尝试 source/加载 `shunit2`（Shell 单元测试框架），但该库未安装在 CI runner 环境中，导致 `[Check]` 阶段的容器验证测试未能执行即崩溃。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增一个 Go 1.25.6 的 Dockerfile 及配套元数据（README.md、image-info.yml、meta.yml），Docker 镜像构建和推送均已完成：

- `#7 DONE 67.8s` — Go 二进制包下载与解压完成
- `#8 DONE 40.5s` — Go 目录结构设置完成
- `#9 DONE 1.5s` — 构建依赖清理完成
- `#11 exporting to image ... DONE 41.9s` — 镜像导出与推送完成
- `[Build] finished` / `[Push] finished` — 构建和推送阶段均成功

失败仅发生在推送后的 `[Check]` 验证阶段，原因是 CI runner 的测试框架缺少 `shunit2` 依赖，属于基础设施问题，与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的测试环境中安装 `shunit2` 包。`shunit2` 是 xUnit 风格的 Shell 单元测试框架，通常可通过系统包管理器安装或从 GitHub 下载。需由 CI 运维人员在 runner 镜像/环境中补充该依赖，使容器检查测试能正常执行。

### 方向 2（置信度: 低）
若 `shunit2` 的缺失仅影响 Go 镜像的特定检查场景，可考虑在 `common_funs.sh` 中添加前置检查，当 `shunit2` 不可用时跳过测试并给出警告而非失败退出。但此方向仅作为临时缓解手段，正确方案应为修复 CI 环境。

## 需要进一步确认的点
1. 确认 CI runner 环境中 `shunit2` 是否应已预装（排查是否为本次构建的 runner 镜像版本遗漏）
2. 确认同类项目（如 Go 其他版本或其他 `Others/` 镜像）的 CI 检查是否也受此影响——如果仅此 PR 触发，可能是特定 runner 节点的问题
3. PR 涉及 `aarch64` runner（日志显示 `linux_arm64` 路径），需确认 x86_64 架构的构建 job 日志是否也有相同问题，以及该 job 是否已通过
