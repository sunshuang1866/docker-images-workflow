# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架shunit2缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 构建完成后的 `[Check]` 测试阶段需要加载 `shunit2`（Shell 单元测试框架），但该框架库在 CI runner 上不存在或不在 `PATH` 中，导致 `common_funs.sh` 第 13 行 `. shunit2` 执行失败，整个检查阶段中断，检查结果表为空。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile（httpd 2.4.66 on openEuler 24.03-LTS-SP4）构建和推送阶段均已成功完成：
- `#10 DONE 41.6s` — `./configure && make && make install` 成功
- `#11 DONE 0.1s` — `groupadd`/`useradd`/`sed` 配置成功
- `#12 DONE 0.0s` — `COPY httpd-foreground` 成功
- `#13 DONE 0.1s` — `chmod +x` 成功
- `#14 DONE 31.3s` — 镜像导出和推送成功
- `[Build] finished` / `[Push] finished` 确认构建和推送完成

失败发生在 `[Check]` 后处理阶段，是 CI 基础设施缺少 `shunit2` 库所致，与本次 PR 的 Dockerfile、httpd-foreground、README、meta.yml 和 image-info.yml 变更均无关联。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 包。openEuler 系统中可通过以下方式安装：
- `dnf install shunit2 -y`
- 或确保 `shunit2` 脚本在 `PATH` 可访问的目录中（如 `/usr/bin/shunit2` 或/usr/local/bin/shunit2`）

### 方向 2（置信度: 低）
如果 CI runner 上确实已安装 `shunit2` 但路径配置有问题，检查 `common_funs.sh` 脚本中的 `PATH` 设置是否遗漏了 `shunit2` 的安装路径。

## 需要进一步确认的点
- 确认 `shunit2` 在 openEuler 24.03-LTS-SP4 的包仓库中是否存在（包名可能为 `shunit2` 或 `shunit`），或确认 CI runner 构建环境中 `shunit2` 的实际安装状态与路径
- 确认本次使用的 CI runner 是否为该 PR 的 `meta.yml` 中未指定 `arch` 约束而意外调度到的 runner 上缺少 `shunit2`（参考类似镜像的 meta.yml 是否需要补充 `arch` 字段）

## 修复验证要求
此失败为 infra-error，修复需由 CI 运维人员在 runner 环境上操作，code-fixer 无需也无法在代码层面修复。若后续重新触发 CI 构建，需确认 runner 环境已安装 `shunit2` 后方可验证。
