# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2: file not found, CRITICAL: [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:23:59,481 - INFO - [Build] finished
2026-07-10 09:23:59,481 - INFO - [Push] finished
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 构建节点的 [Check] 阶段依赖 `shunit2`（一个 Bash 单元测试框架），但该框架未安装在 CI runner 环境中。Docker 镜像的编译（422/422 步骤全部通过）、推送（aarch64 push 成功）均正常完成，失败完全由 CI 基础设施缺失测试依赖导致。

### 与 PR 变更的关联
**与 PR 无关。** PR 只为 bind9 新增 openEuler 24.03-LTS-SP4 的 Dockerfile、配置文件（named.conf）及元数据条目。Docker 构建过程完全成功——编译、链接、安装、镜像导出和推送均无错误。失败发生在 CI 自有的容器镜像验证步骤（[Check] phase），该步骤调用 `common_funs.sh` 脚本时需要 `shunit2` 但文件不存在，属于 CI 环境配置问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是标准的 Bash 单元测试库，可通过以下方式之一安装：
- openEuler 包管理器安装（如果可用）
- 从 GitHub 仓库 `kward/shunit2` 克隆到 CI runner 的预期路径
- 确认 `/usr/local/etc/eulerpublisher/tests/common/` 下 `shunit2` 文件是否存在，若缺失则补充

## 需要进一步确认的点
1. 该 CI runner 是否只有 aarch64 构建节点缺失 shunit2，还是所有节点均缺失（本次日志仅展示 aarch64 构建）
2. x86-64 架构的构建 job 是否也存在同样的 [Check] 失败（本次日志中未提供 x86-64 的构建结果）
3. `shunit2` 在 CI runner 中的预期安装路径，以及该文件是否被意外删除或从未安装
