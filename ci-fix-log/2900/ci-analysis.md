# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, [Check] test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在执行 `[Check]` 阶段时，其通用测试脚本 `common_funs.sh` 试图通过 `. shunit2` 引入 `shunit2` shell 单元测试框架，但该框架未安装在 CI runner 环境中（`file not found`），导致所有检查项均未执行（检查结果表为空），整个 Job 被标记为失败。Docker 镜像构建（#9～#14 全部 DONE）和推送（[Push] finished）均已成功完成。

### 与 PR 变更的关联
**与 PR 无关。** PR 变更为纯增量内容：新增 `httpd 2.4.66` 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、启动脚本 `httpd-foreground`，以及 README、meta.yml、image-info.yml 的条目补充。这些文件均不涉及 CI 测试工具 `eulerpublisher` 或 `shunit2` 的安装与配置。Docker 镜像构建阶段也已完全通过，失败仅发生在 CI 基础设施的测试后处理阶段。

## 修复方向

### 方向 1（置信度: 高）
CI runner 环境中缺失 `shunit2` 测试框架包。需在 CI runner 的初始化/置备脚本中安装 `shunit2`（例如通过 `dnf install shunit2` 或 `pip install shunit2` 等方式），确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 能成功 `. shunit2` 引入测试库。

### 方向 2（可选，置信度: 低）
若 `shunit2` 安装后 [Check] 阶段仍失败，则需进一步排查 httpd 容器的运行时测试本身（如容器启动、端口监听、健康检查等），但当前日志中检查结果表为空，无任何运行时错误信息，无法判断。

## 需要进一步确认的点
1. `shunit2` 是否已安装在当前 CI 所有 runner 上？该依赖是否在所有镜像类型（x86_64、aarch64）的 runner 上都缺失，还是仅本 job 的 runner 缺失？
2. 同一时间段内其他 PR（非 httpd）的 [Check] 阶段是否也因相同 `shunit2: file not found` 错误失败？若其他 PR 的 Check 通过，则可能是 httpd 的测试配置触发了不同路径导致 shunit2 需求，需对比类似成功镜像（如 httpd 24.03-lts-sp2）的 CI 日志。
3. 需确认 `eulerpublisher` 版本是否有更新，是否引入了对 `shunit2` 的新依赖而未同步更新 runner 环境。

## 修复验证要求
此问题为 CI 基础设施依赖缺失，不涉及 PR 代码修改。修复后只需重新触发 CI 构建，观察 [Check] 阶段是否通过即可验证。
