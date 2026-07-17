# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39 同类）
- 新模式标题: CI测试框架缺shunit2
- 新模式症状关键词: shunit2: file not found, eulerpublisher, Check test failed

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
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行器上 `shunit2`（Shell 单元测试框架）未安装或不在 `PATH` 中，导致 `eulerpublisher` 在 [Check] 阶段执行容器功能测试时无法 source `shunit2`，测试框架初始化失败，所有检查项（Check Items 表为空）均未执行。

### 与 PR 变更的关联

**与 PR 变更无关。**

PR 仅新增了以下文件：
- `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`（新 httpd 2.4.66 on openEuler 24.03-LTS-SP4 镜像）
- `Others/httpd/2.4.66/24.03-lts-sp4/httpd-foreground`（容器启动脚本）

以及更新了 `README.md`、`doc/image-info.yml`、`meta.yml` 等元数据文件。

Docker 镜像构建本身**完全成功**：所有 7 个构建步骤均通过，镜像成功推送至目标仓库（`#14 DONE 31.3s`，`[Build] finished`，`[Push] finished`）。失败仅发生在 CI 编排工具 `eulerpublisher` 的容器功能检查阶段，且直接原因是 CI 运行器环境缺少 `shunit2`，与 PR 新增的 Dockerfile 内容或构建逻辑无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI 运行器环境上安装 `shunit2`（Shell 单元测试框架）。eulerpublisher 的 `common_funs.sh` 在第 13 行尝试 `. shunit2` 加载该测试框架，需确保 `shunit2` 已安装在 `/usr/share/shunit2/shunit2` 或 CI 运行器的 `PATH` 中。

### 方向 2（置信度: 中）
若 `shunit2` 近期从 CI 运行器镜像中被移除（可能是基础镜像升级导致），则需在 CI 流水线的环境准备阶段（如 `docker/Dockerfile` 或 `requirements.sh`）显式安装 `shunit2` 包（openEuler 上包名可能为 `shunit2` 或需从 GitHub 获取）。

## 需要进一步确认的点
1. CI 运行器（`jenkins`）上 `shunit2` 是否已安装？可通过 `rpm -qa | grep shunit2` 或 `which shunit2` 在对应节点上确认。
2. `shunit2` 的缺失是仅影响该 PR 的 httpd 镜像测试，还是会影响所有使用相同 Check 流程的其他镜像构建？建议检查近期其他成功 PR 的 Check 阶段是否也出现过此错误。
3. `common_funs.sh:13` 的实际内容：确认是绝对路径引用还是相对路径引用（如 `. shunit2` 依赖 `PATH`，`. /usr/share/shunit2/shunit2` 则应检查对应路径是否存在）。
