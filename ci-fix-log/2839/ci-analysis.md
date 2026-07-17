# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（CI工具依赖缺失）
- 新模式标题: （不适用）
- 新模式症状关键词: （不适用）

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`（CI 测试框架脚本）
- 失败原因: CI 运行环境中缺少 `shunit2` 测试框架（shell 单元测试工具），导致镜像的 `[Check]` 验证阶段无法执行任何测试。Docker 镜像构建和推送本身均已成功完成（`[Build] finished`、`[Push] finished`，镜像已推送至 docker.io）。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增了 postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh、meta.yml 和 README 条目。Docker 构建阶段（编译安装 PostgreSQL 17.6 + 构建镜像）完全成功，镜像已成功推送。失败发生在 CI 流水线的 `[Check]` 阶段，即 `eulerpublisher` 工具尝试运行容器镜像验证测试时，因 CI runner 未安装 `shunit2` 而导致测试框架初始化失败。这是 CI 基础设施问题，非 PR 代码引入。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是一个 shell 单元测试框架，通常可通过 RPM 包或手动安装到 `/usr/local/etc/eulerpublisher/tests/container/common/` 路径下。需确认 CI runner 镜像或 bootstrap 脚本中包含 `shunit2` 的安装步骤。

## 需要进一步确认的点
- 确认 `eulerpublisher` 容器发布工具在 Check 阶段对 `shunit2` 的依赖路径（`/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`）是否与 CI runner 上的实际 `shunit2` 安装路径一致。
- 确认该 CI runner 上其他同类 postgres 镜像的 Check 阶段是否也存在相同问题（验证是否为此次构建的 runner 环境特定问题，还是该 runner 普遍缺少 `shunit2`）。
