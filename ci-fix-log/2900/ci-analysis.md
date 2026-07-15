# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, line 13

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 运行器（runner）上的 `eulerpublisher` 测试工具在检查阶段尝试 source 加载 `shunit2` Shell 单元测试框架，但该框架未安装或不在预期路径中，导致整个 Check 阶段崩溃。Docker 镜像构建和推送（`[Build] finished`、`[Push] finished`）均已成功完成，失败仅发生在 CI 后处理/测试阶段。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增以下文件：
- `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`（新 Dockerfile）
- `Others/httpd/2.4.66/24.03-lts-sp4/httpd-foreground`（新启动脚本）
- 对 `README.md`、`image-info.yml`、`meta.yml` 的文档/元数据更新

日志显示 Docker 镜像构建第 1-7 步全部成功（`#10 DONE 41.6s`、`#11 DONE 0.1s`、`#12 DONE 0.0s`、`#13 DONE 0.1s`），镜像导出和推送均完成（`#14 DONE 31.3s`）。失败发生在 `eulerpublisher` 工具的 `[Check]` 阶段，因 CI 运行器环境的测试依赖缺失（`shunit2`）导致检查脚本本身无法执行，与 httpd 镜像内容或 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题：需要在 CI runner 环境中安装或配置 `shunit2` Shell 测试框架。`shunit2` 应放置在 `eulerpublisher` 测试工具的 `common_funs.sh` 可 source 到的路径（如 `PATH` 环境变量中或与脚本同目录）。Code Fixer 无需处理，应由 CI 运维团队修复 runner 环境。

### 方向 2（置信度: 低）
若其他同类 PR 的 Check 阶段能正常通过（表明 `shunit2` 在 runner 上是可用的），则可能是本次 CI 运行的并发/竞态问题或临时性环境异常。建议在 CI 修复后重新触发一次运行以验证。

## 需要进一步确认的点
1. 同一 CI runner 上，其他近期同类镜像 PR（如其他 httpd 或 Others 目录下的 PR）的 Check 阶段是否能正常通过（即 `shunit2` 是否存在）。
2. `eulerpublisher` 测试工具中 `common_funs.sh` 对 `shunit2` 的加载路径（是相对路径还是依赖 `PATH`），以及该 runner 的操作系统版本和已安装包列表。
3. `shunit2` 是否是 `eulerpublisher` 工具包的依赖项，是否需要在 CI 环境的构建步骤中显式安装（如 `yum install shunit2` 或 `pip install shunit2`）。

## 修复验证要求
若修复方向涉及正则 patch 外部源文件：不适用（本次失败为 infra-error，与源代码逻辑无关）。
