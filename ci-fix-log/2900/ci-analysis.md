# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI检查依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段中测试框架脚本 `common_funs.sh` 尝试通过 `.`（source）加载 `shunit2` 单元测试库，但该 shell 库文件未安装在 CI runner 环境中，导致所有容器检查测试无法执行，检查结果表为空，eulerpublisher 直接标记为 CRITICAL 失败。

### 与 PR 变更的关联
**与本次 PR 变更无关。** Docker 镜像构建和推送阶段均完全成功（`#10 DONE 41.6s`，`[Build] finished`，`[Push] finished`），httpd 2.4.66 从源码编译、安装、配置、推送到镜像仓库均正常完成。失败仅发生在 CI test runner 的 [Check] 后置验证阶段，因 `shunit2` shell 测试框架库缺失导致 `common_funs.sh` 无法加载依赖，所有容器测试用例均未能运行。

PR 新增的 Dockerfile 和 `httpd-foreground` 脚本在构建阶段未产生任何错误，所添加的文件结构（Dockerfile、httpd-foreground、meta.yml、README.md、image-info.yml）均符合项目规范。

## 修复方向

### 方向 1（置信度: 高）
CI runner 环境中缺少 `shunit2` shell 测试库。需在 CI 测试节点上安装 `shunit2`（如通过 `dnf install shunit2` 或 `pip install shunit2`），或将其部署到 `/usr/local/etc/eulerpublisher/tests/common/` 目录下，使 `common_funs.sh` 能够正确 source 该库文件。此为纯 CI 基础设施维护操作，不涉及任何代码变更。

## 需要进一步确认的点
1. 需确认 openEuler 24.03-LTS-SP4 软件源中 `shunit2` 的包名（可能是 `shunit2` 或 `shUnit2`），以及该包是否在当前 CI runner 节点上可用。
2. 若 `shunit2` 不可通过 dnf 直接安装，需确认 eulerpublisher 项目本身的期望部署方式（是否应作为 eulerpublisher 依赖随包一起分发，还是由 CI 环境管理）。
3. 可对比同类 httpd 其他版本（如 24.03-lts-sp2）的 CI 构建历史，确认该测试节点上同一路径的 `shunit2` 是否在更早时间点可用（如近期测试节点环境变更导致 `shunit2` 被移除或路径变更）。
