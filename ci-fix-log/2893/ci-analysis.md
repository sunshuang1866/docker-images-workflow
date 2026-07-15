# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（CI工具依赖缺失）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-10 09:23:59,481 - INFO - [Build] finished
2026-07-10 09:23:59,481 - INFO - [Push] finished
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 测试框架 `shunit2`（shell 单元测试框架）未安装到 CI runner 的文件系统上，导致 `eulerpublisher` 容器的 `[Check]` 测试阶段无法执行任何测试，直接报 CRITICAL 失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile 和配置文件中：
- Docker 镜像构建阶段全部成功完成（meson 编译 422/422 targets、链接、安装均通过）
- Docker 镜像推送也成功完成（`openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 已推送至 docker.io）
- 失败仅发生在 CI 流水线的 `[Check]`（容器启动后验证）阶段，且根因是 CI runner 上缺失 `shunit2` 测试框架，属于 CI 基础设施问题

## 修复方向

### 方向 1（置信度: 高）
CI 管理员需要在 runner 上安装 `shunit2` 测试框架。`shunit2` 可从其 GitHub 仓库获取（`https://github.com/kward/shunit2`），或者通过系统包管理器安装（如 `dnf install shunit2`），确保 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 第 13 行的 `source shunit2` 能正确找到该文件。

## 需要进一步确认的点
- 确认 `shunit2` 是否在其他 openEuler CI runner 节点上已安装——如果其他镜像的 `[Check]` 测试均正常通过，说明 `shunit2` 仅在该 runner 节点上缺失，无需全局修复，只需修复单个节点
- 确认 `shunit2` 的期望安装路径（`common_funs.sh` 中 `source` 命令依赖 `PATH` 环境变量还是绝对路径），以便准确安装到正确位置
