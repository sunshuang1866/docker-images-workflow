# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39"CI工具依赖缺失"同族，但具体缺失项不同）
- 新模式标题: CI测试框架缺失shunit2
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
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`（shunit2 source 语句）
- 失败原因: CI runner 上 eulerpublisher 测试框架的 `common_funs.sh` 在第 13 行尝试 `source shunit2`，但 `shunit2` shell 测试库未安装在该 runner 上，导致 [Check] 阶段全部测试项均为空结果、无一执行，最终判定测试失败。

Docker 镜像的构建（`[Build]`）和推送（`[Push]`）均已成功完成：
- `#8 DONE 268.4s` — Postgres 源码编译+安装成功
- `#11 DONE 58.0s` — 镜像推送到 registry 成功
- `[Build] finished` / `[Push] finished`

### 与 PR 变更的关联
**无关**。PR 仅新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和 entrypoint.sh，以及对应的 README.md 与 meta.yml 条目。Docker 构建成功证明 PR 代码本身没有问题。`shunit2` 缺失是 CI runner 环境的依赖缺失，属于基础设施问题，并非此 PR 引入。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner（执行 eulerpublisher [Check] 阶段的节点）上安装 `shunit2` shell 测试库。具体操作：在 runner 的初始化脚本或 `eulerpublisher` 安装步骤中确保 `shunit2` 可被 `source` 加载（例如通过 `dnf install shunit2` 或从上游下载 `shunit2` 脚本放置到 `PATH` 路径下）。重试 CI 即可。

### 方向 2（置信度: 低）
若方向 1 不可行（runner 环境由编排层管控无法修改），则需要在 eulerpublisher 的测试入口处改为条件检测 `shunit2` 是否存在，若缺失则跳过测试并输出警告而非报 CRITICAL 失败。此为对 eulerpublisher 工具自身的改进，不在本 PR 范围内。

## 需要进一步确认的点
- 确认该 CI runner 上是否曾正常安装过 `shunit2`，是否为近期 runner 环境变更导致该依赖丢失。
- 确认同一批次的同类 PR（其他 PostgreSQL 版本或其他镜像的新增 PR）是否也因同样原因失败——若是，则可进一步确认非此 PR 特有问题。
- 确认 eulerpublisher 的 `common_funs.sh` 中 `shunit2` 的来源路径（当前仅为裸 `shunit2`，未指定绝对路径），以便正确安装到预期位置。

## 修复验证要求
无需代码修复。CI 管理员在 runner 上安装 `shunit2` 后重跑 CI 即可。若重跑后触发新的失败（如 entrypoint.sh 功能测试不通过），则需重新分析。
