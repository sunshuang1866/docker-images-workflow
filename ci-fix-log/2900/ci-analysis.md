# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（同类——CI 工具依赖缺失，不同具体组件）
- 新模式标题: CI检查shunit2缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, [Check] test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 编排工具 `eulerpublisher` 在 `[Check]` 阶段执行容器测试时，其内置测试框架 `common_funs.sh` 第 13 行尝试 source `shunit2`（Shell 单元测试框架），但 `shunit2` 未安装/不存在于 CI 测试运行环境中。Docker 镜像构建（7/7 步骤全部 DONE）和推送均已成功完成，失败仅发生于 CI 的测试框架初始化阶段。检查结果表完全为空，进一步佐证测试框架本身未能正常启动。

### 与 PR 变更的关联
**无关。** PR 新增的 Dockerfile（`Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`）和配套文件（`httpd-foreground`、`meta.yml` 条目、`README.md` 条目、`image-info.yml` 条目）在 Docker 构建阶段全部执行成功：
- 源包下载及解压（#9 DONE）
- `./configure && make && make install`（#10 DONE 41.6s）
- 用户/权限配置、sed 替换、符号链接（#11 DONE 0.1s）
- COPY 启动脚本（#12 DONE 0.0s）
- chmod（#13 DONE 0.1s）
- 镜像导出并推送（#14 DONE 31.3s）

`[Build] finished` 和 `[Push] finished` 日志证实构建和推送均正常。失败发生在 eulerpublisher 自身的 Check 框架层面，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**CI 运维侧修复**：在 CI 测试 runner 中安装 `shunit2` 或确保 `shunit2` 可被 `common_funs.sh` 的 source 路径找到。参考方式：将 `shunit2` 脚本安装至 `/usr/local/etc/eulerpublisher/tests/container/common/` 或系统 PATH 中的标准位置（如 `/usr/local/bin/shunit2`）。这与 PR 的 Dockerfile / 元数据文件无关，Code Fixer 无需处理。

## 需要进一步确认的点
1. 同一 CI runner 上其他近期通过的镜像 Check（如 faiss、hnswlib 等）是否有各自独立的测试脚本绕过此系统级 shunit2 依赖，掩盖了该 runner 上 long-standing 的 shunit2 缺失问题。
2. CI runner 最近是否经历过环境变更（如 eulerpublisher 版本升级、系统包清理），导致 `shunit2` 从原本存在变为缺失。
3. `common_funs.sh` 第 13 行 source 的 `shunit2` 期望的精确路径是什么（是相对路径还是依赖 `$PATH`），这有助于确定修复方式。
