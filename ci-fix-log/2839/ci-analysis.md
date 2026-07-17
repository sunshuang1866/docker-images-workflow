# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2` 测试框架，导致 `common_funs.sh` 脚本在第 13 行尝试加载 `shunit2` 时失败，[Check] 阶段无法执行任何容器测试（测试结果表为空）。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 Postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh、meta.yml 条目和 README 更新。日志显示 Docker 镜像构建（`[Build] finished`）和推送（`[Push] finished`）均已成功完成，所有 10 个 `RUN`/`COPY` 步骤均正常通过（`#8 DONE 268.4s` / `#10 DONE 0.1s`）。失败发生在 CI 测试框架的 [Check] 阶段——CI runner 环境中 `shunit2`（Shell 单元测试框架）缺失，导致测试脚本初始化时立即失败，未能执行任何实质性的镜像验证测试。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题。需 CI 管理员在 runner 环境中安装 `shunit2`，或确保 `eulerpublisher` 容器镜像测试依赖在 [Check] 阶段执行前已正确安装。Code Fixer 无需处理此 PR。

## 需要进一步确认的点
- 确认 `shunit2` 在 CI runner 上的预期安装路径，以及是否被配置在 `PATH` 或测试脚本的 `source` 路径中
- 检查同一 CI 环境下其他近期成功镜像的 [Check] 阶段是否正常通过，以判断本次是 runner 实例的偶发问题还是持久性配置缺失
