# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 测试框架 shunit2 缺失
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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 的 [Check] 阶段调用 `eulerpublisher` 的测试脚本 `common_funs.sh`，该脚本在第 13 行执行 `. shunit2` 尝试加载 shell 单元测试框架，但 `shunit2` 在 CI runner 环境中未安装或路径不可达。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 构建全部成功：
- 源码下载、解压 (`#9`) — 成功
- configure + make + make install (`#10`) — 成功（`DONE 41.6s`）
- 用户/目录/配置设置 (`#11`) — 成功（`DONE 0.1s`）
- COPY 启动脚本 (`#12`) — 成功
- chmod (`#13`) — 成功
- 导出 + 推送镜像 (`#14`) — 成功（`DONE 31.3s`）

`[Build] finished` 和 `[Push] finished` 均在日志中确认完成。失败仅发生在构建/推送成功之后的 CI 测试框架 [Check] 阶段，根因是 CI runner 上缺少 `shunit2` shell 测试工具，与本次 PR 的 Dockerfile 内容、依赖安装、编译步骤没有任何关系。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境或 eulerpublisher 测试容器中安装 `shunit2` 测试框架。`shunit2` 是一个标准的 shell 单元测试库（通常通过系统的包管理器如 `apt install shunit2` 或 `dnf install shunit2` 安装，也可从 GitHub 下载单一脚本文件部署到指定路径）。具体修复由 CI 基础设施团队处理，不需要修改 PR 中的任何代码。

## 需要进一步确认的点
- 同一 CI runner 上其他已通过检查的镜像（如 httpd 的 24.03-lts-sp2 版本）是否也使用了相同的 `common_funs.sh` + `shunit2` 测试链路。如果它们通过而本次失败，需对比 runner 环境差异或检查本次是否有临时性的依赖丢失。
- `shunit2` 在 openEuler 24.03-LTS-SP4 CI runner 上的安装方式（包名、路径约定）。

## 修复验证要求
无。本次失败为 CI 基础设施问题（infra-error），不涉及 PR 源码修改。
