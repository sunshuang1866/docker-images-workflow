# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: "shunit2 测试框架缺失"
- 新模式症状关键词: "shunit2, No such file or directory, common_funs.sh, Check test failed"

## 根因分析

### 直接错误
```
2026-07-09 09:40:23,529 - INFO - [Build] finished
2026-07-09 09:40:23,529 - INFO - [Push] finished
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13（CI 测试基础设施）
- 失败原因: Docker 镜像构建和推送均**成功完成**（`[Build] finished`、`[Push] finished`），失败发生在 CI 的 `[Check]` 阶段——`common_funs.sh` 脚本尝试 `source` 或执行 `shunit2`（Shell 单元测试框架），但 `shunit2` 未安装在 CI runner 环境中，导致测试脚本加载失败，整个 job 标记为 `FAILURE`。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 新增了 postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和 entrypoint.sh，Docker 构建（含 `./configure && make -j "$(nproc)" && make install`）已成功完成并推送镜像。失败 100% 来源于 CI runner 自身缺少 `shunit2` 测试框架依赖，属于基础设施配置问题，Code Fixer 无需处理 PR 中的任何文件。

## 修复方向

### 方向 1（置信度: 高）
CI 运维/管理员在 runner 节点上安装 `shunit2`（Shell 单元测试框架）。具体操作：在 CI runner 环境中通过包管理器安装（如 `dnf install shunit2` 或 `apt-get install shunit2`），或在测试脚本所用的 `PATH` 目录下手动部署 `shunit2` 可执行文件。

### 方向 2（置信度: 低——不推荐）
将测试框架从 shunit2 切换到其他已安装的 Shell 测试框架（如 bats）。但此方案改动范围大，涉及 `common_funs.sh` 及所有依赖它的测试脚本重写，不建议采用。

## 需要进一步确认的点
1. 验证 `shunit2` 在 openEuler 24.03-LTS-SP4 的包仓库中是否可用（包名可能为 `shunit2` 或 `shunit`）。
2. 确认同架构（x86_64）下其他成功镜像的 `[Check]` 阶段是否也经过同一测试脚本，以判断 `shunit2` 是否为该 runner 节点特有问题。
3. 检查 aarch64 架构的姐妹构建 job 是否也因 `shunit2` 缺失而失败（若日志未提供，需获取验证）。
