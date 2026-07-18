# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段的测试脚本 `common_funs.sh` 第13行尝试加载 `shunit2` 测试框架，但该框架未安装在当前 CI Runner 上（`No such file or directory`）

### 与 PR 变更的关联
**与 PR 变更无关。** 此次 PR 的变更（新增 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh，以及更新 README.md 和 meta.yml）均正常执行完成：

- Docker 构建阶段（`[Build]`）：**成功** — PostgreSQL 17_6 从源码编译、安装全部完成，镜像构建和推送均成功（`#11 DONE 58.0s`）
- 镜像推送阶段（`[Push]`）：**成功** — 镜像 `17.6-oe2403sp4-x86_64` 已推送至 registry
- 容器测试阶段（`[Check]`）：**失败** — 因 CI Runner 缺少 `shunit2` 测试框架，无法执行容器启动/功能验证测试

Dockerfile 本身构建无任何错误，PostgreSQL 编译安装和镜像推流均顺利完成。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 环境中安装 `shunit2` 测试框架。该框架通常可通过包管理器安装（如 `yum install shunit2` 或 `dnf install shunit2`），或从 [GitHub](https://github.com/kward/shunit2) 手动部署至 Runner 的测试脚本可访问路径。

## 需要进一步确认的点
- 确认 CI Runner 镜像/环境中 `shunit2` 是否应预装但遗漏
- 确认该 CI Runner 是否与其他成功执行 Check 步骤的 Runner 使用相同环境配置
- 确认是否存在替代的测试脚本路径（不含 shunit2 依赖）可用于验证该镜像

## 修复验证要求
无需代码修复验证。此错误为 CI 基础设施问题，与 PR 提交的 Dockerfile、entrypoint.sh 或 meta.yml 无关。
