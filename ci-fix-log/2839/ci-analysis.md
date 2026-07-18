# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39"CI工具依赖缺失"同类但症状不同）
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 CRITICAL - [Check] test failed

+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 测试框架脚本 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试运行器上缺少 `shunit2` shell 单元测试框架（参考 https://github.com/kward/shunit2），导致 [Check] 阶段的测试框架初始化失败，所有检查项均未执行（检查结果表为空）。Docker 镜像构建（`#8 DONE 268.4s`）和推送（`[Push] finished`）均已成功完成。

### 与 PR 变更的关联
**无关。** PR 变更内容为新增 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh、README 文档更新、meta.yml 元数据注册。这些变更不会影响 CI 测试框架的依赖。`shunit2: No such file or directory` 是 CI runner 环境配置问题，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施修复**：在 CI 测试 runner（`ecs-build-docker-*` 节点）上安装 `shunit2` shell 测试框架。对于使用 `eulerpublisher` 进行镜像测试的 runner，执行 `dnf install -y shunit2` 或从 GitHub（`kward/shunit2`）手动安装至测试框架的搜索路径中。此修复由 CI 运维团队在 runner 环境层面执行，Code Fixer 无需处理 PR 代码。

## 需要进一步确认的点
- 确认 `shunit2` 是否被其他成功构建的 PR 的 Check 阶段使用（如果是，则可能是本次 runner 节点环境差异导致），可从相同场景目录（Database/postgres/）的其他成功构建记录验证
- 确认日志中仅出现 x86_64 架构的构建和推送（标签 `17.6-oe2403sp4-x86_64`），aarch64 架构的构建日志是否缺失——若 `meta.yml` 未加 `arch: x86_64` 约束，需确认 aarch64 构建是否也失败及其原因
