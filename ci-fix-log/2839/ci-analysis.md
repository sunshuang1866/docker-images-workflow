# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh

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
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 环境的 [Check] 测试阶段在加载 `common_funs.sh` 时尝试执行 `shunit2` 命令，但该测试框架二进制/脚本在 CI runner 环境中不存在。Docker 镜像构建（`#8 DONE 268.4s`）和推送（`[Push] finished`）均成功完成，Check 结果表为空说明所有测试项均未能执行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 `Database/postgres/17.6/24.03-lts-sp4/Dockerfile`、`entrypoint.sh`、README 更新和 `meta.yml` 条目，Docker 构建阶段全部通过（编译、安装、分层、推送均成功）。失败发生在 eulerpublisher 框架的 [Check] 镜像验证环节，因 CI runner 缺少 `shunit2` 测试框架依赖导致所有测试项无法执行。这是 CI 基础设施问题，非代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
联系 CI 基础设施运维团队，确认本次 CI runner 环境中是否安装了 `shunit2` 测试框架。若缺失，需在该 runner 镜像/节点上安装 `shunit2`（如 `dnf install shunit2` 或通过 pip 安装），确保 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 可以正常引用 `shunit2`。

## 需要进一步确认的点
- 本次 CI 使用的是什么类型的 runner（如 `ecs-build-docker-x86-64-*` 或 `ecs-build-docker-aarch64-*`），该 runner 的镜像模板中是否预装了 `shunit2`。
- 同一 CI 流水线中其他同类镜像（如其他 postgres 版本、其他 Database 镜像）的 [Check] 阶段是否正常工作，以判断是本次 runner 环境孤例问题还是全局性问题。
- 是否需要由运维统一在 `eulerpublisher` 的基础 runner 镜像中加入 `shunit2` 依赖，避免后续新镜像 PR 反复遇到同类问题。

## 修复验证要求
非代码修复，无需 code-fixer 介入。若运维确认 `shunit2` 已安装但仍失败，需进一步检查 `common_funs.sh` 中对 `shunit2` 的引用路径是否正确。
