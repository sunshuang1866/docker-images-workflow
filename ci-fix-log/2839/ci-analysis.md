# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh

## 根因分析

### 直接错误
```
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试环境缺少 `shunit2` shell 测试框架，`common_funs.sh` 在 line 13 `source` 它时找不到该文件，导致 [Check] 阶段直接失败，所有测试用例均未执行（Check Results 表为空）

### 与 PR 变更的关联
**与 PR 无关。** 日志显示 Docker 镜像构建 (`[Build] finished`) 和推送 (`[Push] finished`) 均成功完成，镜像 `17.6-oe2403sp4-x86_64` 已正确构建并推送至 registry。失败仅发生在 CI 流水线的后置检查阶段 ([Check])，是因 CI runner 自身缺少 `shunit2` 依赖导致的，并非 PR 文件（Dockerfile、entrypoint.sh、meta.yml、README.md）引入的问题。

## 修复方向

### 方向 1（置信度: 高）
CI 管理员需在构建 runner 上安装 `shunit2`（如通过 `dnf install shunit2` 或手动部署脚本到 `/usr/local/etc/eulerpublisher/tests/` 目录）。此问题与 PR 代码变更无关，Code Fixer 无需处理。

## 需要进一步确认的点
- 确认 CI runner 环境中 `shunit2` 是否曾经存在但被误删，还是该 runner 从未安装过此测试框架
- 确认其他同类 PR 的 [Check] 阶段是否也因同样原因失败（以排除特定镜像/架构 runner 的局部环境问题）
