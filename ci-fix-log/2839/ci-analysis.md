# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 宿主环境 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 的 `[Check]` 测试阶段，测试脚本 `common_funs.sh` 尝试 source `shunit2`（Shell 单元测试框架），但 `shunit2` 未安装在 CI Runner 上，脚本立即失败退出。Check 结果表为空（无任何测试项运行），说明在容器启动检查之前就已经因为测试框架缺失而退出。

### 与 PR 变更的关联
**与 PR 无关**。Docker 镜像构建（包括 PostgreSQL 源码编译 `./configure && make -j "$(nproc)" && make install`）已完整成功完成：

- `#8 DONE 268.4s` — PostgreSQL 17.6 编译和安装全部通过
- `#11 DONE 58.0s` — 镜像导出并推送成功
- `[Build] finished`、`[Push] finished` — 构建和推送阶段均正常

PR 新增的 Dockerfile（安装 shadow-utils、编译 PostgreSQL、复制 entrypoint.sh）和 entrypoint.sh 均未影响 CI Runner 上测试框架的可用性。`shunit2` 缺失是 CI 基础设施层面的问题，与本次代码变更无关。BuildKit 的两个 `LegacyKeyValueFormat` 警告（line 26、line 30 的 `ENV` 格式）仅为 lint 提示，非致命错误。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 环境中安装 `shunit2` 测试框架。`shunit2` 是一个标准的 Shell 单元测试库，可通过包管理器安装（如 `dnf install shunit2`）或手动下载部署到 `/usr/local/etc/eulerpublisher/tests/` 所期望的路径下。

## 需要进一步确认的点
- CI Runner 上 `shunit2` 的预期安装位置和版本（当前报错路径为 CI 工具的测试脚本目录，需确认 shunit2 是应随 `eulerpublisher` 包附带还是独立安装）
- 该 Runner 上其他 PR 的 `[Check]` 阶段是否也出现同样错误（以确认是 Runner 级问题还是该 Job 配置遗漏了依赖安装步骤）
