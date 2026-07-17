# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI缺少shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 测试框架 `eulerpublisher` 的公共脚本 `common_funs.sh` 尝试 `. shunit2` 导入 shunit2 测试库，但 shunit2 未安装在 CI runner 上，导致 [Check] 阶段的容器验证测试完全无法执行（测试结果表为空）。

### 与 PR 变更的关联
**与 PR 变更无关**。Docker 镜像构建和推送均成功完成（`[Build] finished` + `[Push] finished`），`#14 DONE 31.3s`。PR 新增的 Dockerfile、httpd-foreground 脚本及元数据文件均正确完成构建。失败发生在 CI 流水线的 [Check] 阶段——这是 eulerpublisher 工具对已构建镜像进行容器启动验证的后置步骤，因 CI runner 环境缺失 `shunit2` 依赖而崩溃。

## 修复方向

### 方向 1（置信度: 中）
CI runner 环境缺少 `shunit2`（shell 单元测试框架）。需要在执行 Check 步骤的 CI runner 上安装 `shunit2`（例如通过 `dnf install shunit2` 或 `pip install shunit2`），确保 eulerpublisher 的测试脚本能正常初始化。

### 方向 2（置信度: 低）
如果该问题仅影响 openEuler 24.03-LTS-SP4 相关镜像的 Check 阶段（即其他 OS 版本的 httpd 镜像 Check 可正常通过），则需要排查 eulerpublisher 的测试配置是否缺少针对 SP4 的基础设施适配（如特定版本的测试镜像、测试数据等），但当前日志中的 `shunit2: file not found` 直接指向 CI runner 层面缺失依赖，不应是版本适配问题。

## 需要进一步确认的点
1. 确认 CI runner 上是否安装了 `shunit2`（执行 `which shunit2` 或检查 `/usr/share/shunit2/` 等默认路径是否存在）
2. 确认同一 CI runner 上其他 PR 的 [Check] 阶段是否能正常执行（若其他镜像的 Check 也失败，则是 CI 基础设施普遍问题）
3. 确认 eulerpublisher 的 `common_funs.sh` 第 13 行中 `shunit2` 的预期来源路径（是系统 PATH 中的命令、同目录文件、还是 pip 安装的模块）
