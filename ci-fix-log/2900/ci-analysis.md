# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI检查框架缺失shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed, eulerpublisher

## 根因分析

### 直接错误
```
#11 [5/7] RUN groupadd -r www-data && useradd -r --create-home -g www-data www-data && ...
#11 DONE 0.1s
#12 [6/7] COPY httpd-foreground /usr/local/bin
#12 DONE 0.0s
#13 [7/7] RUN chmod +x /usr/local/bin/httpd-foreground
#13 DONE 0.1s
#14 exporting to image
#14 exporting layers 11.7s done
2026-07-10 09:18:18,406 - INFO - [Build] finished
2026-07-10 09:18:18,406 - INFO - [Push] finished
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh`:13（`. shunit2` source 语句）
- 失败原因: CI 检查阶段运行时，`eulerpublisher` 测试框架的 `common_funs.sh` 脚本在第 13 行尝试 source 加载 `shunit2`（Shell 单元测试框架），但该文件在 CI Runner 的文件系统中不存在，导致所有测试用例无法注册执行，check 结果表为空，最终标记为 FAILURE。

### 与 PR 变更的关联
与本次 PR 变更**无关**。Docker 镜像构建（7/7 步骤全部通过）和镜像推送均已完成并成功。Dockerfile 中引入的 `httpd-foreground` 入口脚本及 `httpd.conf` sed 配置修改在实际构建阶段未报任何错误。失败发生在 CI 流水线的后置检查阶段，属于 CI Runner 基础设施缺少 `shunit2` 依赖的问题。

## 修复方向

### 方向 1（置信度: 中）
在 CI Runner 节点上安装 `shunit2` 包（如 `dnf install shunit2` 或 `yum install shunit2`），确保 `/usr/share/shunit2/shunit2` 或 `common_funs.sh` 预期路径下存在该框架文件。此为纯 CI 基础设施修复，Code Fixer 无需处理 PR 代码。

## 需要进一步确认的点
1. 确认 CI Runner 上 `shunit2` 包是否已安装及其实际路径（可通过 `rpm -ql shunit2` 或 `which shunit2` 验证）。
2. 确认 `common_funs.sh` 中 source `shunit2` 的路径期望（相对路径还是绝对路径），判断是否需要安装后创建符号链接。
3. 确认其他同类 PR（如相同的 24.03-lts-sp4 Dockerfile 添加）是否也存在同样的 check 阶段失败——若为系统性现象，则进一步确认是 infra 问题。

## 修复验证要求
无需验证 PR 代码变更，但建议 CI 管理员：
1. 在此 PR 的 CI runner 上安装 `shunit2` 后重新触发构建；
2. 确认 check 结果表能正确填充内容（至少应有容器启动检查等基本测试项），而非空表。
