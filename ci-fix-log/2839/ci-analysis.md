# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上 `eulerpublisher` 的 [Check] 阶段（`common_funs.sh:13`）
- 失败原因: CI 测试框架 `eulerpublisher` 的 Shell 脚本 `common_funs.sh` 尝试加载 `shunit2`（Shell 单元测试库），但该工具未安装在 CI Runner 的基础环境中，导致所有 [Check] 测试项无法加载执行，检查结果表为空

### 与 PR 变更的关联
**与 PR 变更无关**。Docker 镜像的构建（`make`, `make install`, 268 秒）和推送（`[Build] finished`, `[Push] finished`）均已完成。日志显示 Postgres 17.6 源码成功编译安装，镜像导出并推送至镜像仓库。失败仅发生在 `eulerpublisher` 的后构建验证阶段（`[Check]`），根因是 CI Runner 基础环境缺少 `shunit2` 测试框架，与 PR 新增的 Dockerfile、entrypoint.sh、README.md、meta.yml 内容无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 基础环境中安装 `shunit2` 测试框架，或将该依赖添加到 `eulerpublisher` 的安装依赖中。`shunit2` 可通过 `yum install shunit2` 或从 GitHub 获取安装。安装完成后 [Check] 阶段可正常加载测试用例并执行容器运行验证。

### 方向 2（置信度: 低）
若 `shunit2` 已安装在 Runner 上但不在 `PATH` 中，需在 `common_funs.sh` 中指定 `shunit2` 的绝对路径，或调整 CI Runner 的 `PATH` 环境变量。

## 需要进一步确认的点
1. 确认该 CI Runner 节点上 `shunit2` 是否应预装，还是需要在该镜像的测试配置中单独声明依赖
2. 确认是否存在专门针对 `postgres` 镜像的 [Check] 测试定义文件，若有且缺失则需一并补充
3. 对比同系列其他 postgres 镜像（如 `postgres:17.6-oe2403sp2`）的 CI Check 是否也因同原因失败，以判断是全局 Runner 环境问题还是仅限本 PR
