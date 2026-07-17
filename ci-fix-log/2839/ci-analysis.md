# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI [Check] 阶段的测试脚本 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架依赖 `shunit2`（Shell 单元测试框架）在当前 runner 环境中缺失，导致容器镜像的 `[Check]` 测试阶段无法加载测试脚本，立即失败。

关键证据：
1. **Docker 镜像构建成功**：PostgreSQL 17.6 的 `./configure && make && make install` 完整执行完毕（`#8 DONE 268.4s`），所有构建产物正确安装到 `/usr/local/pgsql/`
2. **镜像推送成功**：日志明确显示 `[Build] finished` 和 `[Push] finished`，镜像已成功推送到 `docker.io/****test/postgres:17.6-oe2403sp4-x86_64`
3. **Check 阶段秒级失败**：从 `09:40:24,013` 到 `09:40:24,021` 仅 8ms，说明 `common_funs.sh` 尝试 `source` 或调用 `shunit2` 时立即失败，测试框架本身未能启动，容器内的实际功能未曾被验证
4. **BuildKit 的两个 Warning（非致命）**：Dockerfile 第 26、30 行的 `ENV key value` 使用了 legacy 格式，BuildKit 产生了 `LegacyKeyValueFormat` 警告，但这**不是**失败原因——构建实际成功完成

### 与 PR 变更的关联
**无关联**。PR 仅新增了以下文件：
- `Database/postgres/17.6/24.03-lts-sp4/Dockerfile` — PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile
- `Database/postgres/17.6/24.03-lts-sp4/entrypoint.sh` — 容器入口脚本
- `Database/postgres/README.md` — 文档更新（新增一行表格条目）
- `Database/postgres/meta.yml` — 元数据更新（新增一个版本条目）

所有新增代码的 Docker 构建阶段均顺利完成。失败发生在 CI 自有的容器验证工具链（`eulerpublisher` Check 阶段），与 PR 提交的代码逻辑无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 测试框架。当前执行 `[Check]` 的 runner 缺少该依赖，导致任何需要容器运行时验证的镜像构建流水线都会在 Check 阶段失败。这是一个 **CI 基础设施问题**，需要运维人员在 runner 镜像或流水线环境中补充 `shunit2` 包。

### 方向 2（置信度: 低）
如果 `shunit2` 已在 runner 上安装但路径未正确配置，检查 `common_funs.sh` 中引用 `shunit2` 的方式（如硬编码路径 vs 依赖 `$PATH`），调整测试脚本使其能正确定位安装的 `shunit2` 二进制/库文件。

## 需要进一步确认的点
- `shunit2` 是否已在执行 `[Check]` 的 runner 节点上安装？可登录 runner 执行 `which shunit2` 或检查 `/usr/local/bin/shunit2`、`/usr/bin/shunit2` 是否存在
- 该 runner 节点上其他同类镜像（如 postgres 17.6 on 24.03-lts-sp2、postgres 17.5 on 24.03-lts-sp1 等）的 Check 测试是否也失败？如果是，则确认为 runner 级别的 `shunit2` 缺失问题
- 如果是 runner 近期环境变更导致 `shunit2` 丢失，可查询 runner 的配置变更历史定位回退点

## 修复验证要求
无需通过修改代码验证。修复后重新触发 CI 流水线，若 `[Check]` 阶段通过（显示具体的检查项结果而不仅仅是空表格），则确认修复生效。
