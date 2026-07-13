# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2 框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, CRITICAL: [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI [Check] 阶段 — eulerpublisher 测试框架的 `common_funs.sh:13`
- 失败原因: CI 测试运行环境中缺少 `shunit2`（Shell 单元测试框架），`common_funs.sh` 尝试 `source` 该文件时失败，导致整个测试表格为空，[Check] 阶段判定失败。

### 与 PR 变更的关联
Docker 镜像的构建阶段（#1-#13 全部通过）和推送阶段均成功。日志显示：
- httpd 2.4.66 源码 configure、make、make install 全部成功完成
- 镜像构建 7/7 步骤全部 `DONE`
- 镜像成功推送到 `docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`

PR 的 Dockerfile 和辅助文件（httpd-foreground）本身没有问题。失败发生在 CI 流水线的镜像检测（[Check]）阶段，是 CI runner 测试环境缺少 `shunit2` 依赖导致，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 中）
CI runner 环境中安装 `shunit2` 包。`shunit2` 是 eulerpublisher 测试框架的运行时依赖，应在所有 CI 测试节点上预装。可从 EPEL 或 GitHub 获取安装：
- openEuler 环境：`dnf install -y shunit2`（如果仓库提供）
- 或从 `https://github.com/kward/shunit2` 下载到 CI runner 的路径搜索范围内

### 方向 2（置信度: 低）
若 `shunit2` 是所有其他应用镜像测试也都需要的依赖，且仅本次 CI 运行失败，可能是 CI runner 节点故障或配置漂移导致的偶发问题。可尝试重试 CI job 验证是否为瞬态 infra 故障。

## 需要进一步确认的点
1. 同一 CI job 的历史运行记录中，[Check] 阶段是否一直正常（即 `shunit2` 在此 runner 上是否本应存在）——若历史成功运行过，则本次是 infra 瞬态故障；若从未成功，则是环境缺失问题。
2. 确认 eulerpublisher 测试框架依赖清单中是否明确列出了 `shunit2`，以及 CI runner 镜像中是否预装了该包。
3. 由于日志中仅看到 x86_64（`-x86_64` 后缀的镜像 tag），需确认 aarch64 架构的下游构建 job 是否也存在相同问题（含 `shunit2` 缺失的报错），或 aarch64 job 已成功。
