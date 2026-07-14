# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39
- 新模式标题: (N/A)
- 新模式症状关键词: (N/A)

## 根因分析

### 直接错误
```
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
- 失败位置: CI 运行环境 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 编排工具 `eulerpublisher` 在 [Check] 阶段执行容器健康检查时，测试框架脚本 `common_funs.sh` 尝试 source `shunit2`（Shell 单元测试库），但该文件在 CI runner 上不存在，导致所有容器检查项全部跳过，检查结果表为空。

### 与 PR 变更的关联
**无关。** Docker 镜像构建（#9-#13 全部 DONE）和推送（[Build] finished, [Push] finished）均已成功完成。镜像已成功构建并推送到仓库（`docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`）。失败仅发生在构建成功后的容器健康检查阶段，是 CI runner 环境缺少 `shunit2` 测试框架导致的，与 PR 新增的 Dockerfile、httpd-foreground 脚本及元数据文件变更无关。

日志中出现的 `LegacyKeyValueFormat` 警告（Dockerfile 第 5 行 `ENV HTTPD_PREFIX /usr/local/apache2` 格式）是 Docker BuildKit 的非致命提示，不影响构建结果。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护方需在构建节点上安装 `shunit2` 包（或修复 `eulerpublisher` 容器测试框架的依赖分发机制，确保测试脚本能正确 source 到 shunit2 库）。此修复不涉及 PR 代码的任何变更。

## 需要进一步确认的点
- CI 维护方确认 `shunit2` 包在该构建节点上是否已安装、路径是否正确。如果是 eulerpublisher 容器化部署的方式运行测试，确认容器镜像内是否包含 shunit2 及其在 `$PATH` 中的位置。
