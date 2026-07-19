# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2依赖缺失
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
Finished: FAILURE
```

### 根因定位
- 失败位置: CI [Check] 阶段，`common_funs.sh:13`
- 失败原因: CI Runner 上缺少 `shunit2` shell 测试框架包，导致镜像构建后的健康检查脚本无法加载 shunit2 库，[Check] 阶段直接失败。Docker 镜像的构建（`#10 DONE 41.6s`）和推送（`#14 DONE 31.3s`）均已完成且成功。

### 与 PR 变更的关联
**与 PR 无关**。PR 变更仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（含 httpd-foreground 启动脚本）及对应的元数据/文档更新。镜像构建阶段（下载源码 → 编译 → 安装 → 配置 → 推送到 registry）全部成功完成。失败仅发生在构建后的 `[Check]` 阶段，原因为 CI 运行环境缺少 `shunit2` 包，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 的操作系统上安装 `shunit2` 包（openEuler 中可通过 `dnf install shunit2` 安装）。此为 CI 基础设施层面的修复，无需修改任何 PR 代码。

## 需要进一步确认的点
- 确认 CI Runner 的操作系统版本和包管理器配置，以便正确安装 `shunit2`。
- 确认该 CI Runner 是否也承载其他镜像的 `[Check]` 测试——如果是，则安装 `shunit2` 后需回归验证其他已有镜像的 Check 阶段也正常工作。
