# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 测试环境 `/usr/local/etc/eulerpublisher/tests/common/` 目录
- 失败原因: CI [Check] 阶段运行时，公共测试脚本 `common_funs.sh` 第 13 行尝试 source `shunit2` 测试框架，但该文件在 CI Runner 上不存在，导致容器启动测试无法执行，整个 Check 阶段失败。

### 与 PR 变更的关联
与 PR 变更**无关**。Docker 镜像构建阶段全部成功完成（Dockerfile 7 个构建步骤均 DONE，镜像已成功构建并推送至 docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64）。失败仅发生在后续的 [Check] 容器运行时测试阶段，原因是 CI 基础设施中缺少 `shunit2` 单元测试框架。PR 新增的 Dockerfile、httpd-foreground 脚本以及 README/image-info.yml/meta.yml 元数据更新均未涉及 CI 测试框架的安装或配置。

日志中 `LegacyKeyValueFormat` 警告（Dockerfile 第 5 行 `ENV HTTPD_PREFIX /usr/local/apache2`）为非致命告警，不是失败根因。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 测试环境安装 `shunit2` 单元测试框架。`shunit2` 是 Shell 脚本单元测试框架（如 https://github.com/kward/shunit2），需确保其可被 `/usr/local/etc/eulerpublisher/tests/common/common_funs.sh` 脚本通过相对路径或标准路径 source 到。

### 方向 2（置信度: 低）
如果 `shunit2` 是作为 CI 环境初始化的一部分（如通过系统包管理器或 setup 脚本安装），排查该初始化步骤为何在此次构建中未生效（如依赖的安装源不可用、环境变量未正确设置等）。

## 需要进一步确认的点
- `shunit2` 是否在其他同类镜像（如 httpd 2.4.66-oe2403sp2）的 CI Check 阶段也缺失，还是仅此次构建出现（需对比同仓库其他成功 PR 的 Check 日志）
- CI Runner 的环境初始化脚本是否最近有变更导致 `shunit2` 安装步骤被跳过
- `/usr/local/etc/eulerpublisher/tests/common/` 目录下 `shunit2` 的预期来源（RPM 包、Git 克隆还是预置文件）

## 修复验证要求
不适用 — 此为 CI 基础设施问题，PR 代码本身无需修改。Code Fixer 无需处理此 PR。
