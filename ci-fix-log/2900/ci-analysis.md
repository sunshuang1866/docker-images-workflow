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
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段使用的测试运行器 `eulerpublisher` 在其测试公共脚本 `common_funs.sh` 第 13 行尝试通过 `. shunit2` 加载 shell 单元测试框架 `shunit2`，但该框架未安装在 CI runner 上，导致所有检查项无法启动，检查结果表为空。

### 与 PR 变更的关联
- **与 PR 无关**。Docker 镜像的构建（7/7 步骤全部 DONE）和推送（Push finished）均已成功完成，镜像已产出并推送到 registry。
- 失败发生在 CI 流水线的 [Check] 后置验证阶段，属于 CI 基础设施层 `eulerpublisher` 测试工具缺少运行时依赖 `shunit2` 的问题。
- PR 变更仅包含新增 Dockerfile、httpd-foreground 入口脚本、README.md 表格条目、image-info.yml 条目和 meta.yml 条目，均为标准镜像添加操作，不可能导致 CI runner 上 `shunit2` 缺失。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架（如在 openEuler 上通过 `dnf install shunit2` 或等效方式安装），使 `eulerpublisher` 的 [Check] 阶段能够正常加载测试基础设施并执行容器镜像的启动/功能验证。此修复不涉及 PR 代码变更，需由 CI 基础设施维护者执行。

## 需要进一步确认的点
1. `shunit2` 是否本应是 `eulerpublisher` 包的依赖项但未被声明，需确认 `eulerpublisher` 的 RPM spec 或 pip setup 中是否遗漏了该运行时依赖。
2. 其他近期 PR 在 CI [Check] 阶段是否也因同样原因失败，以判断这是本次 CI runner 的单点故障还是全局性基础设施退化。
