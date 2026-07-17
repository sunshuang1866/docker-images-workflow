# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
```

Check 阶段的结果表格为空（无任何检查项被执行）：
```
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 环境中缺少 `shunit2` 单元测试框架库（shell 测试框架），导致 Check 阶段的测试脚本无法加载该依赖而直接失败，未执行任何实际检查

### 与 PR 变更的关联
**与 PR 代码变更无关。** 证据如下：

1. Docker 镜像构建阶段（7/7 步骤）全部成功完成：`#10 DONE 41.6s`（编译安装）、`#11 DONE 0.1s`（配置）、`#12 DONE 0.0s`（COPY）、`#13 DONE 0.1s`（chmod）
2. 镜像导出和推送成功：`#14 DONE 31.3s`，日志明确显示 `[Build] finished` 和 `[Push] finished`
3. 失败发生在 `[Check]` 阶段——该阶段使用的 `common_funs.sh` 脚本是 CI 工具链（`eulerpublisher`）的内置文件，试图 `source shunit2` 但因 CI 环境中未安装该 shell 测试框架而失败。错误发生在 `common_funs.sh` 第 13 行，根本没进入容器测试逻辑

注：日志中出现的 `LegacyKeyValueFormat` warning（Dockerfile 第 5 行 `ENV HTTPD_PREFIX /usr/local/apache2` 应写成 `ENV HTTPD_PREFIX=/usr/local/apache2`）仅是一个构建警告，不是导致失败的根因。

## 修复方向

### 方向 1（置信度: 中）
在 CI Runner 环境中安装 `shunit2` 包。openEuler 仓库中一般对应的包名为 `shunit2`，但需确认 `eulerpublisher` 测试脚本（`common_funs.sh`）所期望的 `shunit2` 文件路径（`source shunit2` 会搜索 `$PATH` 或已安装路径）。若无法在 CI 环境安装，则需要确认 CI 工具链版本是否与 openEuler 24.03-LTS-SP4 的 Runner 环境兼容。

### 方向 2（置信度: 低）
如果 `shunit2` 已在大多数 CI Runner 上可用，而仅在 24.03-LTS-SP4 对应的 Runner 上缺失，则可能是该架构/job 的 Runner 镜像配置遗漏了 `shunit2` 依赖的安装步骤，属于 CI 编排配置问题。

## 需要进一步确认的点

1. CI 构建日志中的 `#9` 步骤（解压 `httpd.tar.gz`）是否存在完整的错误输出被截断——日志仅显示了解压后的文件列表，需确认该步骤无隐藏的编译错误
2. 同一 CI Runner 上其他镜像（如已有的 `2.4.66-oe2403sp2`）的 Check 阶段是否能通过，以确认 `shunit2` 缺失是特定于 sp4 runner 还是全局性问题
3. `eulerpublisher` 测试框架对 `shunit2` 的实际安装路径要求（确认是包名 `shunit2` 还是需从源码安装）
4. 检查 `meta.yml` 中新增的 `2.4.66-oe2403sp4` 条目是否缺少 `arch` 约束——虽然当前构建在 x86_64 上成功了，但如果镜像同时需要 aarch64 构建，需确认 meta.yml 配置完整

## 修复验证要求
若修复方向涉及 CI Runner 环境变更（安装 shunit2），code-fixer 无法直接操作 CI 基础设施。若需从 Dockerfile 层面规避该问题（如通过自定义检查脚本绕过 `common_funs.sh`），则需验证该方案在所有已支持的 httpd 版本（2.4.66-oe2403sp2、2.4.51-oe2203lts、2.4.58-oe2203sp3 等）上的兼容性，确保不破坏现有镜像的 Check 流程。
