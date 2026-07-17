# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:23,529-...-INFO: [Build] finished
2026-07-09 09:40:23,529-...-INFO: [Push] finished
2026-07-09 09:40:24,013-...-INFO: [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-...-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 的测试脚本 `common_funs.sh` 第 13 行尝试加载 `shunit2`（Shell 单元测试框架），但 `shunit2` 在 CI runner 环境中不可用（未安装或路径未配置），导致测试框架初始化失败，[Check] 阶段无法执行任何容器测试，所有检查项为空，最终 CRITICAL 失败。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 新增的 Dockerfile 和 entrypoint.sh 在 [Build] 和 [Push] 阶段均已成功完成：
- PostgreSQL 17.6 从源码编译成功（`make -j "$(nproc)" && make install`，约 268 秒完成）
- Docker 镜像构建成功（`#11 exporting to image ... DONE`）
- 镜像推送成功（`[Push] finished`，镜像已推送到 `docker.io/****test/postgres:17.6-oe2403sp4-x86_64`）

失败仅发生在后续的 CI [Check] 阶段，原因是 CI runner 测试基础设施缺少 `shunit2` 依赖，属于 CI 环境配置问题。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 节点上安装 `shunit2` 测试框架并确保其在 Shell 的 `PATH` 中或 `common_funs.sh` 中 `source` 的路径正确可访问。`shunit2` 通常通过包管理器安装（如 `dnf install shunit2`）或手动部署到 `/usr/local/etc/eulerpublisher/tests/` 相关路径下。

### 方向 2（置信度: 低）
如果 `shunit2` 确实已安装在 CI runner 上，则可能是 `common_funs.sh` 中 `source` 或 `.` 引用的 `shunit2` 路径不正确，需要修正脚本中的路径引用。

## 需要进一步确认的点
1. CI runner 节点上是否安装了 `shunit2`，可通过 `which shunit2` 或 `rpm -qa | grep shunit2` 确认
2. `common_funs.sh` 第 13 行 `shunit2` 的具体加载方式（是 `source shunit2`、`. shunit2` 还是其他形式），确定它期望 `shunit2` 存在于哪个路径
3. 确认同仓库其他 PR 的 CI [Check] 阶段是否也出现相同错误（若其他 PR 正常通过 Check，则可能是本次 runner 节点的特定环境异常）
4. 查看完整的 `common_funs.sh` 内容以确认第 13 行完整代码上下文
