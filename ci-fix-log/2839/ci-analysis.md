# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 流水线 [Check] 阶段中 `eulerpublisher` 测试框架的 `common_funs.sh` 脚本尝试 source `shunit2`（Shell 单元测试框架），但 CI runner 环境中未安装 `shunit2`，导致测试脚本本身启动失败，无法执行任何镜像校验。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 仅新增了以下文件：
- `Database/postgres/17.6/24.03-lts-sp4/Dockerfile`（新增）
- `Database/postgres/17.6/24.03-lts-sp4/entrypoint.sh`（新增）
- `Database/postgres/README.md`（新增 1 行表格条目）
- `Database/postgres/meta.yml`（新增 2 行镜像配置）

Docker 镜像构建和推送均已完成且成功（日志中 `#8 DONE 268.4s`、`[Build] finished`、`[Push] finished`、manifest 推送成功），PostgreSQL 17.6 源码编译 `./configure && make -j "$(nproc)" && make install` 无任何编译错误。失败完全发生在 CI 自身的 [Check] 后处理阶段，因 runner 缺少 `shunit2` 依赖所致。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2`。`shunit2` 是一个标准 Shell 单元测试框架，通常在 openEuler 上可通过包管理器安装（如 `dnf install shunit2`），或从 GitHub releases 下载后放入 `PATH`。此修复由 CI 运维团队执行，Code Fixer 无需处理 Dockerfile 或任何 PR 代码。

## 需要进一步确认的点
- 确认 CI runner 的 [Check] 阶段是否本应预装 `shunit2`，以及是否因 runner 镜像版本或其他因素导致该依赖缺失。
- 确认同类 24.03-lts-sp4 平台的其他镜像（如其他 Database 镜像）的 [Check] 阶段是否同样因缺少 `shunit2` 而失败，以判断是通性问题还是仅影响该 job。
