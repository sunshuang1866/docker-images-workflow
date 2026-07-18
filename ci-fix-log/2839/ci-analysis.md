# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI缺失shunit2测试框架
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 基础设施测试脚本）
- 失败原因: CI [Check] 阶段在执行容器镜像功能验证时，`eulerpublisher` 测试框架的 `common_funs.sh` 尝试 source `shunit2`（Bash 单元测试框架），但 `shunit2` 未安装在当前 CI runner 上，导致检查脚本无法运行，整个 pipeline 标记为失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增了 postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和 entrypoint.sh。Docker 构建阶段已完全成功：
- `#8 DONE 268.4s` — PostgreSQL 源码编译完成，所有 `make install` 步骤正常结束
- `[Build] finished` / `[Push] finished` — 镜像构建和推送均成功
- 镜像已推送到 `docker.io/****test/postgres:17.6-oe2403sp4-x86_64`

失败仅发生在构建完成后的 `[Check]` 阶段，原因是 CI runner 自身缺少 `shunit2` 测试框架依赖，与 PR 中提交的 Dockerfile、entrypoint.sh、README.md、meta.yml 均无关联。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题，**Code Fixer 无需处理**。需要 CI 运维人员确保负责 postgres 镜像检查的 CI runner 上安装 `shunit2`（例如通过 `dnf install shunit2` 或在 runner 初始化脚本中预置该工具）。

## 需要进一步确认的点
- 确认该 CI runner（执行 postgres 镜像检查的节点）的 `shunit2` 安装状态，对比其他同类 postgres 分支（如 24.03-lts-sp2、22.03-lts-sp4）的 CI runner 是否也不同程度缺少该依赖。
- 确认是否因为 openEuler 24.03-LTS-SP4 的 runner 节点是新分配的，其环境初始化未包含 `shunit2`。
