# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI Runner 环境中缺少 `shunit2` Shell 测试框架，导致 [Check] 阶段无法执行 PostgreSQL 镜像的启动/功能验证测试。Docker 镜像的构建和推送均已完成且成功（日志中 `[Build] finished`、`[Push] finished` 及 `#11 DONE 58.0s` 均为成功标志）。

### 与 PR 变更的关联
**与 PR 无关**。PR 新增了 postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和 entrypoint.sh，镜像构建阶段（`./configure && make -j "$(nproc)" && make install` 及后续 `COPY`/`RUN chmod` 步骤）全部顺利通过，镜像已成功推送到 docker.io。失败发生在 CI 流水线工具 `eulerpublisher` 的 [Check] 阶段，该阶段调用 `common_funs.sh` 脚本行 `source shunit2` 时因 CI Runner 未安装该 Shell 测试框架而报错。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 环境中安装 `shunit2` Shell 测试框架（如通过 `dnf install shunit2` 或 `yum install shunit2`），使 `common_funs.sh` 能正确 source 该库并执行 PostgreSQL 镜像的冒烟测试。此为纯 CI 基础设施问题，无需修改 PR 中的 Dockerfile 或 entrypoint.sh。

## 需要进一步确认的点
- 该 CI Runner 上是否应该预装 `shunit2`？是本次构建节点未正确配置，还是此节点的标准环境就不包含 `shunit2`？
- 同类仓库中其他 PR 的 [Check] 阶段是否也因同样原因失败？若为全局性问题，则需在 CI Runner 镜像/置备脚本中补充 `shunit2` 的安装步骤。
