# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（概念上类似 模式39：CI工具依赖缺失）
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: No such file or directory, common_funs.sh, [Check] test failed

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
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 工具 `eulerpublisher` 内置测试脚本）
- 失败原因: CI Check 阶段的 shell 测试框架 `shunit2` 在 CI runner 上不存在，`common_funs.sh` 第 13 行尝试 source `shunit2` 时失败。Docker 镜像的构建（`make -j` + `make install`）和推送均已完成且成功，失败仅发生在 CI 后置检查阶段。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 `Database/postgres/17.6/24.03-lts-sp4/Dockerfile`、`entrypoint.sh` 和更新了 `meta.yml`/`README.md`。Docker 镜像构建 100% 成功（所有 11 个构建步骤均 `DONE`），镜像已成功推送到 registry。失败发生在 CI 工具链 `eulerpublisher` 的 `[Check]` 阶段，该阶段由 `/usr/local/etc/eulerpublisher/tests/` 下的 shell 测试脚本驱动，其依赖的 `shunit2` 框架在当前 runner 环境中缺失。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` shell 测试框架（如在 openEuler 24.03-LTS-SP4 上 `yum install shunit2` 或将其部署到 PATH 可见路径），确保 `/usr/local/etc/eulerpublisher/tests/common/common_funs.sh` 能正常 source 该框架。此为纯 CI 基础设施修复，无需修改 PR 中的任何代码文件。

## 需要进一步确认的点
- 确认该 CI runner 是否为新部署的 24.03-LTS-SP4 runner，可能缺少完整的测试依赖包
- 如果同一 runner 上其他同类 postgres 镜像（如 `17.6/24.03-lts-sp2`）的 Check 阶段能通过，则确认具体差异（不同镜像路径是否有不同的测试入口、`shunit2` 安装路径是否因镜像 tag 而异）
- CI 日志中的 2 个 `LegacyKeyValueFormat` 警告（ENV key=value 格式）为非致命信息，与本次失败无关，无需处理

## 修复验证要求
N/A（本次为 infra-error，不由 code-fixer 修复）
