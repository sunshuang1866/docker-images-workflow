# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（参照: 模式39 CI工具依赖缺失）
- 新模式标题: CI检查框架依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

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
- 失败位置: CI Runner [Check] 阶段，eulerpublisher 测试框架内 `common_funs.sh:13`
- 失败原因: CI 测试框架 `shunit2`（Shell 单元测试框架）在 CI Runner 上未安装或路径不可达，`common_funs.sh` 第 13 行 `source shunit2` 失败。检查结果表为空——说明没有任何测试实际执行，[Check] 阶段在启动时就崩溃了。

### 与 PR 变更的关联
**与 PR 变更无关。** 证据如下：
- Docker 镜像构建全部成功：`./configure`、`make`、`make install` 均通过（#10 DONE 41.6s）
- 全部 7 个 Dockerfile 步骤均标记 `DONE`（#9 到 #13）
- 镜像导出和推送成功（#14 DONE 31.3s，manifest pushed）
- [Build] finished、[Push] finished 均正常输出
- 唯一的失败点 `shunit2: file not found` 发生在 CI 自身的检查框架中，是 CI Runner 环境问题，非 PR 代码可控制

该 PR 仅新增：Dockerfile、httpd-foreground 启动脚本、README.md 更新、image-info.yml 更新、meta.yml 更新。这些变更均不涉及 CI 基础设施配置。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` 测试框架，或修正 `common_funs.sh` 中 `shunit2` 的引用路径使之指向正确安装位置。此问题属于 CI 运维范畴，**Code Fixer 无需处理 PR 代码**。

## 需要进一步确认的点
- CI Runner 镜像中 `shunit2` 是否应为预装组件——若为预装，检查 Runner 镜像版本或初始化脚本是否有回退
- 同一时间段内其他同类 PR（如其他应用镜像的新增版本）是否也遇到相同错误，以判断是全局 CI 环境问题还是单次瞬态故障
- `common_funs.sh` 中 `shunit2` 的预期安装路径和当前 Runner 实际路径是否一致
