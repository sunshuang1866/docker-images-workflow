# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI [Check] 阶段的通用测试脚本 `common_funs.sh` 尝试通过 `. shunit2` 引入 shUnit2 shell 测试框架，但该框架在 aarch64 构建节点的 runner 上未安装或不在预期的加载路径中，导致测试脚本执行失败。

### 与 PR 变更的关联
**此次失败与 PR 变更无关。** 证据如下：
1. Docker 构建阶段全部成功——bind9 9.21.23 源码在 openEuler 24.03-LTS-SP4 上通过 meson 编译完成（422/422 个编译目标全部通过）。
2. Docker 推送阶段成功——镜像 `openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 已成功推送到 registry。
3. 失败仅发生在构建/推送完成后的 [Check] 阶段，错误为 CI 测试框架依赖缺失（`shunit2: file not found`），属 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 aarch64 架构的 CI runner（`ecs-build-docker-aarch64-01-sp` 或同类节点）上安装 `shunit2` 测试框架包，确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 的 `. shunit2` 语句能找到所需的 shell 库文件。

### 方向 2（置信度: 低）
若 `shunit2` 已安装但存放路径与 `common_funs.sh` 期望的 `PATH` 或相对路径不一致，调整 CI runner 上 `shunit2` 的安装路径或测试脚本的 source 路径。

## 需要进一步确认的点
1. 该 CI runner 的 aarch64 节点上是否安装了 `shunit2`（openEuler 上的包名可能是 `shunit2` 或 `ShellUnit`）。
2. 同一镜像的 amd64 构建节点是否存在同样的 shunit2 缺失问题（本次日志仅覆盖 aarch64 构建，amd64 结果未知）。
3. 其他最近在 aarch64 上构建的 PR 的 [Check] 阶段是否也因同一原因失败——若为普遍问题，需统一修复 runner 环境。

## 修复验证要求
无需 code-fixer 验证（本失败为 infra-error，不涉及代码或 Dockerfile 修改）。
