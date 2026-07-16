# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
#10 DONE 41.6s
...
#13 DONE 0.1s
#14 exporting to image
#14 pushing layers 15.8s done
#14 DONE 31.3s
2026-07-10 09:18:18,406 - INFO - [Build] finished
2026-07-10 09:18:18,406 - INFO - [Push] finished
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
- 失败原因: CI 测试运行器（eulerpublisher）的 Check 阶段脚本 `common_funs.sh` 尝试 source `shunit2`（Shell 单元测试框架），但该工具未安装在 CI runner 上，导致测试框架初始化失败，进而整个 Check 阶段报 `CRITICAL: [Check] test failed`。

### 与 PR 变更的关联
**与 PR 变更完全无关**。PR 变更内容为新增 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件。Docker 镜像的构建（`#10` `#11` `#12` `#13` 全部 DONE）和推送（`[Build] finished`、`[Push] finished`）均已成功完成。失败发生在 CI 管道的后置 Check 阶段，根因是 CI runner 环境缺少 `shunit2` 依赖，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI 测试 runner 环境中安装 `shunit2` 包。例如在 openEuler 上使用 `dnf install shunit2`，或在 CI 任务配置中将 `shunit2` 脚本部署到指定路径（如 `/usr/local/etc/eulerpublisher/tests/container/common/`）。

## 需要进一步确认的点
- CI runner 的 `shunit2` 安装位置和方式，需确认是否需要在 CI 编排脚本中添加安装步骤。
- 其他 openEuler 24.03-LTS-SP4 镜像的 Check 阶段是否也受此影响（即是否为该 runner 的全局问题）。
