# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 环境 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13（Check 阶段，非代码仓库内文件）
- 失败原因: CI 的 `[Check]` 阶段中，测试脚本 `common_funs.sh` 尝试 `source`（`.` 命令）`shunit2` shell 测试框架时，该文件在 CI runner 环境中不存在。注意 `[Check]` 从启动到失败仅 10 毫秒（`09:24:00,652` → `09:24:00,662`），说明失败发生在测试脚本的初始化阶段，而非实际功能测试。

### Docker 构建阶段全部通过（作为对照证据）
- meson setup/compile/install 三个阶段均正常完成，全部 422 个编译目标链接成功
- 最终二进制 `named` 成功链接（`[422/422] Linking target named`）
- 镜像导出 & 推送成功：`#13 DONE 36.0s`
- INFO 日志确认：`[Build] finished` 和 `[Push] finished` 均无异常
- 日志中标注镜像架构为 `aarch64`（`openeulertest/bind9:9.21.23-oe2403sp4-aarch64`）

### 与 PR 变更的关联
与 PR 变更**无关**。本次 PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Docker 镜像（Dockerfile + named.conf + 元数据更新），Docker 构建本身在所有阶段均通过。失败发生在 CI 平台的 `[Check]` 测试阶段，属于 CI 基础设施层面的问题（测试框架 shunit2 未安装或路径配置错误）。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施团队需确认 `shunit2` 在 aarch64 runner 节点上是否已安装。若未安装，安装 `shunit2` 到 CI runner 的标准测试路径下，使 `common_funs.sh` 能正确 source 该框架后，重新触发 CI 验证。

### 方向 2（置信度: 低）
若 `shunit2` 已安装但路径不同，需检查 CI runner 上的 `PATH` 环境变量或测试脚本中的 `shunit2` 路径引用，确保与安装位置一致。

## 需要进一步确认的点
1. 本次 PR 的 x86_64 (amd64) 架构构建 job 是否也因同样原因失败，还是仅 aarch64 架构失败。日志仅提供了 aarch64 架构的构建 & 检查日志，需要获取 x86_64 对应 job 的日志进行交叉验证
2. 同一 CI runner 上其他镜像的 `[Check]` 阶段是否也出现 `shunit2: file not found` 错误，以判断该问题是本次新增还是长期存在的 infra 缺陷
3. CI runner 上 `shunit2` 的实际安装路径及 `common_funs.sh` 中引用 `shunit2` 的 source 机制（绝对路径 vs 相对路径 vs PATH 搜寻）

## 修复验证要求
（不适用——本失败为 CI 基础设施问题，无需对代码仓库中的 PR 文件做任何修改。）
