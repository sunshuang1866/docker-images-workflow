# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 测试阶段的 `eulerpublisher` 框架在执行镜像 [Check] 验证时，`common_funs.sh` 尝试 `source shunit2` 但该 shell 测试框架未安装在当前 runner 节点上，导致所有检查项为空表，测试阶段直接失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增的 Dockerfile 构建完全成功——所有 7 个 Docker 构建步骤（安装依赖、configure/make/make install、配置修改、COPY 启动脚本等）均顺利通过，镜像已成功构建并推送至 registry（`[Build] finished` → `[Push] finished`）。失败发生在 CI 自身的 `eulerpublisher` Check 阶段，是 runner 环境缺少 `shunit2` 测试框架所致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 节点上安装 `shunit2` shell 测试框架包。openEuler 系统可通过以下方式之一安装：
- `dnf install shunit2`（如果 openEuler 仓库已有该包）
- 或从 `https://github.com/kward/shunit2` 手动部署到 runner 的 `/usr/local/etc/eulerpublisher/tests/` 可发现路径

## 需要进一步确认的点
1. 确认该 runner 节点上 `shunit2` 是否曾经可用、是否为近期环境变更导致丢失
2. 确认同一 runner 上其他镜像的 [Check] 测试是否也因同一原因失败（若其他镜像也受影响，则可确认是全局性 infra 问题）
3. 确认 `eulerpublisher` 的部署脚本或环境初始化流程是否遗漏了 `shunit2` 依赖声明
