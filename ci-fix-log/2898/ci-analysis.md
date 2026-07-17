# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, Check, test failed, common_funs.sh

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 运行环境 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 节点的 [Check] 阶段测试脚本 `common_funs.sh` 尝试加载 `shunit2`（Shell 单元测试框架），但该工具未安装在 CI runner 环境中，导致测试脚本执行失败。

### 与 PR 变更的关联

**与 PR 变更无关。** Docker 镜像构建（`[Build]`）和推送（`[Push]`）阶段均已成功完成：
- `#7 DONE 67.8s` — Go 1.25.6 下载解压成功
- `#8 DONE 40.5s` — 文件时间戳和符号链接创建成功
- `#9 DONE 1.5s` — 构建依赖清理成功
- `#10 DONE 0.0s` — WORKDIR 设置成功
- `#11 DONE 41.9s` — 镜像导出、分层推送、manifest 推送全部成功
- 日志明确记录：`[Build] finished`、`[Push] finished`

失败仅发生在构建/推送完成后的容器运行检查（`[Check]`）阶段，原因是 CI runner 上缺少 `shunit2` 测试框架，与 PR 新增的 Dockerfile 及元数据文件无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2`，使其对 `common_funs.sh` 中的 `source shunit2` 可用。常见的安装方式：
- `dnf install shunit2 -y`（若 openEuler 仓库有该包）
- 或将 `shunit2` 脚本下载到 CI runner 的 PATH 路径中

此为 CI 基础设施维护工作，无需修改任何 PR 代码。

## 需要进一步确认的点
- 该 CI runner 节点上是否原本安装了 `shunit2`，是本次运行前被误移除还是在特定 runner 上缺失
- 同一集群中其他 runner 节点是否也存在 `shunit2` 缺失问题（若为个别节点问题，可能是节点配置遗漏）
- `shunit2` 在 openEuler 24.03-LTS-SP4 仓库中的包名和可用性（可能需要加 EPOL 或其他第三方源）
