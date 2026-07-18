# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13（`eulerpublisher` CI 工具的测试框架脚本）
- 失败原因: `eulerpublisher` 在 [Check] 阶段的测试脚本 `common_funs.sh` 尝试 `source shunit2`（Shell 单元测试框架），但 CI runner 环境中未安装 `shunit2`，导致测试框架初始化失败，所有测试用例均无法加载执行（Check 结果表为空）。

### 与 PR 变更的关联
**本次 PR 变更与失败无关。** PR 仅新增了 `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile` 和 `httpd-foreground` 脚本，以及 README、image-info.yml、meta.yml 等元数据文件。Docker 镜像构建全部 7 个步骤成功完成：
- `#10 DONE 41.6s` — 源码编译（`./configure && make && make install`）成功，httpd 2.4.66 编译安装完成
- `#11 DONE 0.1s` — `groupadd`/`useradd` 创建用户、`sed` 配置修改成功
- `#12 DONE 0.0s` — `COPY httpd-foreground` 成功
- `#13 DONE 0.1s` — `chmod +x` 成功
- 镜像导出、推送均成功：`[Build] finished` → `[Push] finished`

失败发生在推送完成之后、CI 工具 `eulerpublisher` 执行容器功能测试（[Check]）阶段，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 中）
CI runner 环境缺少 `shunit2` 包。需在 CI 编排配置中为运行 `eulerpublisher` 测试的 runner 预装 `shunit2`（openEuler 上可能通过 `dnf install shunit2` 安装）。此问题不影响 Docker 镜像本身的正确性，Code Fixer 无需对 PR 中的 Dockerfile 或元数据文件做任何修改。

## 需要进一步确认的点
1. `shunit2` 在当前 CI runner 环境中是否预期已安装（即这是一次性的环境缺失还是系统性配置遗漏）。需要查看 CI runner 初始化脚本中是否有安装 `shunit2` 的步骤。
2. 同为 openEuler 24.03-LTS-SP4 的其他近期 PR 的 [Check] 阶段是否也出现相同错误。如果其他 SP4 仓库的 Check 也都失败，说明这是 SP4 runner 环境的系统性配置缺失。
3. `shunit2` 在 openEuler 24.03-LTS-SP4 上的准确包名（可能为 `shunit2` 或 `shUnit2`），以及是否在默认仓库中可用。

## 修复验证要求
无需验证——本失败为 CI 基础设施问题，不涉及任何代码修复。PR 中的 Dockerfile 构建、推送均已完成且成功，镜像 `****test/httpd:2.4.66-oe2403sp4-x86_64` 已生成并可用。
