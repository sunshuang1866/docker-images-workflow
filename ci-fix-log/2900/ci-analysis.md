# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed, eulerpublisher

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
- 失败位置: CI [Check] 阶段 — `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在执行容器检查脚本时，`common_funs.sh` 尝试通过 `source` 命令加载 `shunit2`（Shell 单元测试框架），但 `shunit2` 未安装在 CI runner 的测试执行环境中，导致测试脚本无法运行、检查结果表为空，CI 最终判定 `[Check] test failed`。

### 与 PR 变更的关联
与 PR 代码变更**完全无关**。从日志可见：
1. Docker 镜像构建完全成功：`#10 DONE 41.6s`（编译 httpd 2.4.66）、`#11 DONE 0.1s`（用户/权限配置）、`#12 DONE 0.0s`（COPY 启动脚本）、`#13 DONE 0.1s`（chmod）
2. Docker 镜像推送完全成功：`[Build] finished`、`[Push] finished`，镜像已推送至 `docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`
3. 失败发生在`[Check]`阶段的测试基础设施层面——`shunit2` 工具未安装，属于 CI runner 环境问题

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的测试执行环境中安装 `shunit2` 包（或确保 `shunit2` 脚本路径在 `eulerpublisher` 测试框架的搜索范围内），使容器健康检查脚本能正常 sourcing `shunit2` 并执行测试用例。此修复完全在 CI 运维侧，**无需修改 PR 中的任何代码文件**。

## 需要进一步确认的点
- 确认其他同类 PR 是否也在此 runner 上遇到相同的 `shunit2: file not found` 问题——如果是，说明是 CI 环境的**系统性缺陷**，需 CI 维护方统一修复
- 确认 `shunit2` 的预期安装路径和版本，以便 CI 运维侧补装
