# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（CI工具依赖缺失，症状有别但根因同类）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI [Check] 阶段，`eulerpublisher` 测试框架文件 `common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2` shell 测试框架，`common_funs.sh` 在第13行尝试加载 `shunit2` 时失败，导致整个 [Check] 阶段崩溃，所有检查项均未实际执行（检查结果表为空）

### 与 PR 变更的关联
**与 PR 完全无关。** PR 变更仅新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和 entrypoint.sh，以及更新 README.md 和 meta.yml。Docker 镜像构建和推送均已成功完成（日志中可见 `[Build] finished`、`[Push] finished` 以及 `#11 DONE 58.0s` 推送完成）。编译阶段（`make`、`make install`）无任何错误。失败仅发生在构建后的 CI 测试验证阶段，原因是 CI 运行环境中缺少 `shunit2` 测试框架。

## 修复方向

### 方向 1（置信度: 高）
CI 管理员需在 `ecs-build-docker-x86_64` runner 上安装 `shunit2` 测试框架。`shunit2` 是 `eulerpublisher` 容器测试依赖，用于执行镜像的功能验证。安装后重新触发 CI 即可通过。

### 方向 2（置信度: 低）
若 `shunit2` 仅在部分 runner 上缺失，CI 调度配置可能需要调整，确保 postgres 镜像的 Check 阶段被调度到已安装 `shunit2` 的 runner 上。

## 需要进一步确认的点
- 确认 `shunit2` 是否是 CI runner 标准镜像的预装组件，还是需要单独安装
- 确认同一 CI 流水线中其他镜像（如已有的 postgres 17.6 on 24.03-LTS-SP2）的 Check 阶段是否同样失败，以判断这是新 runner 的普遍问题还是仅影响特定 job
- 确认 openEuler 24.03-LTS-SP4 的 CI runner 镜像是否缺少 `shunit2` 包（与旧版 runner 相比是否有包列表变化）
