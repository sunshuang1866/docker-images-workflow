# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 编排工具 eulerpublisher 的容器检查阶段（`[Check]`），具体在 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI runner 上缺少 `shunit2`（Shell 单元测试框架），导致 eulerpublisher 的容器检查脚本在执行 `source shunit2` 时找不到该文件，整个 Check 阶段终止并标记为失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 及更新元数据文件。Docker 镜像的构建和推送阶段均成功完成：
- 编译阶段：422/422 个目标全部成功编译和链接
- 安装阶段：所有二进制文件、库文件、man 手册均正确安装
- 推送阶段：镜像 `openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 成功推送到 Docker Hub

`shunit2` 缺失错误发生在 CI 系统的公共测试脚本 `common_funs.sh` 中，属于 CI 基础设施层面的依赖缺失，与 PR 的代码变更无因果关系。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2`。`shunit2` 是一个 Shell 单元测试框架，通常可通过包管理器安装（如 `dnf install shunit2` 或 `pip install shunit2`）或以 standalone 脚本方式部署到 `/usr/local/bin/` 或 `/usr/local/lib/` 路径下。需确认 eulerpublisher 的 `common_funs.sh` 期望从哪个路径 source `shunit2`，确保文件存在于对应位置。

### 方向 2（置信度: 低）
若 `shunit2` 已安装在 CI runner 上但路径配置有误，则需检查 `common_funs.sh` 中 source `shunit2` 的查找路径（是否依赖 `PATH`、`SHUNIT2_HOME` 等环境变量），修复路径配置。

## 需要进一步确认的点
1. CI runner 环境上是否已安装了 `shunit2`？若未安装，需确认 eulerpublisher 对该依赖的版本要求和安装方式。
2. `common_funs.sh` 第 13 行 source `shunit2` 时使用的是相对路径、绝对路径还是依赖环境变量？这决定安装后是否需要额外配置。
3. 该 CI 失败是否仅影响 bind9 的 SP4 镜像检查，还是同一 runner 上其他镜像的 Check 阶段也会因此失败（需跨 PR 对比验证）。

## 修复验证要求
- 修复后，需重新触发 CI 流水线，确认 `[Check]` 阶段不再报 `shunit2: file not found`，且容器检查测试能够正常通过。
- 若 CI 在 `[Check]` 阶段有实际的容器启动/功能测试（如检查 named 进程是否正常启动），需一并验证这些测试是否通过，避免 `shunit2` 修复后暴露出其他潜在的容器运行时问题。
