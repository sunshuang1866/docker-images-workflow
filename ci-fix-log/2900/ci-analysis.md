# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 缺少 `shunit2` 测试框架，导致容器镜像的 `[Check]` 后置校验阶段脚本 `common_funs.sh` 无法 source `shunit2`，整个检查步骤崩溃。Docker 镜像的构建（`[Build]`）和推送（`[Push]`）均已成功完成。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 变更仅为新增 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套文件（httpd-foreground 脚本、README.md 更新、image-info.yml 更新、meta.yml 更新）。日志显示 Docker 镜像从编译到推送全过程成功（`#10 DONE 41.6s`、`#11 DONE 0.1s`、`#12 DONE 0.0s`、`#13 DONE 0.1s`、`#14 推送成功`），失败仅发生在 CI 平台后置校验阶段——该阶段因 Runner 环境缺少 `shunit2` 工具而无法执行任何检查条目（检查结果表完全为空）。

## 修复方向

### 方向 1（置信度: 高）
CI Runner 环境缺少 `shunit2`（Shell 单元测试框架）。需由 CI 基础设施团队在 Runner 镜像中安装 `shunit2` 包，确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 在第 13 行的 `. shunit2` 能找到该文件。此问题为 CI 平台侧环境缺陷，PR 代码无需任何修改。

## 需要进一步确认的点
- 确认 CI Runner 镜像的构建流程中 `shunit2` 是否被遗漏安装，或安装路径是否不符合 `common_funs.sh` 的 source 搜索路径（`PATH` / `SHUNIT2_HOME`）。
- 确认同一 CI Runner 上其他仓库/PR 的 `[Check]` 阶段是否也受此影响（若为近期 Runner 镜像更新引起，可能是一个系统性故障）。
