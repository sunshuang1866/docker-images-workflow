# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2依赖缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

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
- 失败位置: CI [Check] 测试阶段，`/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI runner 环境中缺少 `shunit2`（Shell 单元测试框架），`common_funs.sh` 第 13 行尝试 `source shunit2` 时找不到该文件，导致所有镜像检查结果为空表，最终 [Check] 阶段判定失败。

### 与 PR 变更的关联
**此失败与 PR 代码变更无关。** Docker 镜像的构建（`#10 DONE 41.6s`）和推送（`#14 DONE 31.3s`）均已成功完成。PR 新增的 Dockerfile、httpd-foreground 脚本、meta.yml、README.md 和 image-info.yml 均不存在语法或逻辑问题。失败完全发生在 CI 流水线的 Check 测试阶段，由 CI runner 缺少 `shunit2` 依赖导致，属于纯基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` Shell 测试框架。`shunit2` 可通过以下方式获取：
- openEuler 仓库：`dnf install shunit2`（如果可用）
- 或从 GitHub 手动部署：`git clone https://github.com/kward/shunit2.git` 并设置 `SHUNIT2_HOME` 环境变量

### 方向 2（可选）
若短期内无法修复 CI 环境的 shunit2 依赖，可检查该镜像的 Check 阶段是否为必选项，考虑暂时跳过 Check 阶段以允许合并。

## 需要进一步确认的点
- 确认 `shunit2` 在 CI runner 上是否曾经安装过，是近期被意外移除还是从未安装
- 确认同为 openEuler 24.03-LTS-SP4 的其他镜像（如 PR #2896、#2894 等）在 Check 阶段是否也遭遇了相同的 `shunit2` 缺失问题
- 确认 CI runner 镜像模板中 `shunit2` 的安装步骤是否需要补充
