# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI 测试框架依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:161]-INFO: [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
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
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI Runner 的 eulerpublisher 测试框架中 `common_funs.sh` 脚本尝试通过 `. shunit2` 加载 Shell 单元测试库 `shunit2`，但该库在 Runner 的文件系统或 `PATH` 中不存在，导致所有 Check 阶段测试无法执行，测试结果表为空，最终判定构建失败。

### 与 PR 变更的关联
与 PR 变更**无关**。Docker 镜像构建（包括 yum 安装依赖、configure、make、make install、容器配置）和推送均完全成功（日志中所有 Docker BuildKit 步骤 `#9` 至 `#14` 均以 `DONE` 完成，镜像成功推送至 registry）。失败发生在构建完成之后的 eulerpublisher `[Check]` 阶段，属于 CI Runner 环境缺少 `shunit2` 测试库依赖的基础设施问题。

日志中 `### Error lines` 部分出现的 `httpd-2.4.66/docs/error/` 等行是 `tar -zvxf` 解压时的文件列表输出（因路径包含 `error` 字符串被 CI 日志解析器误分类为错误行），并非真正的错误。

## 修复方向

### 方向 1（置信度: 中）
在 CI Runner 上安装 `shunit2` Shell 单元测试框架。对于 openEuler 环境，可通过 `yum install shunit2` 或 `dnf install shunit2` 安装，或从源码（如 GitHub 上的 kward/shunit2）部署到 `/usr/local/etc/eulerpublisher/tests/container/common/` 目录下。

### 方向 2（置信度: 低）
如果 `shunit2` 不是 Runner 全局依赖而是应由测试脚本所在目录自包含的库，则需要检查 eulerpublisher 测试框架的部署方式，确保 `shunit2` 文件随 eulerpublisher 包一起安装。

## 需要进一步确认的点
- 确认同一 CI Runner 上其他非 httpd 镜像的 PR 是否也能在 Check 阶段正常通过。如果其他镜像的 Check 也失败，则 Runner 环境普遍缺少 `shunit2`；如果只有本 PR 失败，则可能存在路径或权限差异。
- 确认 `shunit2` 在 Runner 上预期的安装路径（是否应在 `/usr/local/etc/eulerpublisher/tests/container/common/` 下，或系统 PATH 中）。
- 确认 eulerpublisher 的版本和部署方式是否发生了变化，导致 `shunit2` 不再随包安装。
- 查看该 Runner 的历史构建记录，判断 `shunit2` 丢失的时间点（是偶发性故障还是环境变更导致的持续性问题）。

## 修复验证要求
无需代码修复验证。此问题属于 CI 基础设施层面，需运维人员检查 Runner 环境后确认修复。
