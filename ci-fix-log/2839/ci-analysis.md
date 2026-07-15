# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 测试框架依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, Check test failed

## 根因分析

### 直接错误
```
[Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: CI [Check] 阶段，`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（shunit2 测试框架加载步骤）
- 失败原因: CI 测试环境（`eulerpublisher` 容器测试框架）缺少 `shunit2` shell 单元测试工具，导致 `[Check]` 阶段无法启动任何测试用例

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 只新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh、README.md 更新和 meta.yml 更新。日志显示 Docker 镜像的编译（make/make install）、构建（`#8 DONE 268.4s`）、推送（`[Push] finished`）均成功完成。失败发生在构建后的镜像检查测试阶段，系 CI 基础设施（`eulerpublisher` 测试框架）缺少 `shunit2` 依赖所致。

## 修复方向

### 方向 1（置信度: 高）
CI 运行环境需安装 `shunit2` 测试框架。该依赖缺失与 PR 代码无关，无需修改 Dockerfile、entrypoint.sh、README.md 或 meta.yml。应联系 CI 运维团队在 `eulerpublisher` 容器测试运行环境中补充 `shunit2`，或检查 `common_funs.sh` 中 `shunit2` 的引用路径是否正确。

## 需要进一步确认的点
- 确认 `shunit2` 是否应作为 `eulerpublisher` 安装包的一部分随工具分发（类似模式39中 `distroless` 模块缺失的情况）
- 确认同一 CI 环境下的其他镜像 PR 是否也遭遇相同的 `[Check]` 阶段失败（若属普遍现象则进一步佐证 infra-error 判断）
- 确认 runner 节点上 `shunit2` 的预期安装路径（`/usr/bin/shunit2`、`/usr/local/bin/shunit2` 等），检查 `common_funs.sh:13` 的 `source` 或引用方式
