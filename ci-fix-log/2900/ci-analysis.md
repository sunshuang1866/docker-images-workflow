# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试环境的 `common_funs.sh` 脚本尝试通过 `.` 命令加载 `shunit2` shell 单元测试框架，但该框架未安装在 CI runner 上，导致测试脚本无法加载，[Check] 阶段在 6 毫秒内立即失败。后续检查结果表也为空（无任何测试用例被执行），进一步证实测试框架不可用。

### 与 PR 变更的关联
与 PR 完全无关。Docker 镜像构建和推送均已成功完成：

- `#10 DONE 41.6s` — httpd 2.4.66 编译和 make install 完整通过
- `#11 DONE 0.1s` — groupadd/useradd/sed 配置全部成功（openEuler 24.03-LTS-SP4 基础镜像已包含 shadow-utils，无需额外安装 shadow 包）
- `#12 DONE 0.0s` / `#13 DONE 0.1s` — httpd-foreground 复制和权限设置正确
- `#14 DONE 31.3s` — 镜像导出和推送正常
- `[Build] finished` / `[Push] finished` 均正常

失败仅发生在 CI 基础设施的 [Check] 后处理阶段，与本次 PR 新增的 httpd 2.4.66/24.03-lts-sp4 Dockerfile、httpd-foreground 脚本、meta.yml、image-info.yml、README.md 均无关联。

## 修复方向

### 方向 1（置信度: 高）
CI runner 上缺失 `shunit2` shell 测试框架。需由 CI 管理员在 runner 环境中安装 shunit2 包（如 `dnf install shunit2`），或修正测试脚本中 shunit2 的加载路径使其指向正确的安装位置。Code Fixer 无需对 PR 代码做任何修改。

## 需要进一步确认的点
- 确认 CI runner 环境中 `shunit2` 的预期安装路径和包管理方式（dnf install shunit2、yum install shunit2 或手动部署）
- 确认该 [Check] 阶段失败是否仅影响本 PR，还是所有在该 runner 上执行 [Check] 阶段的 PR 都会遇到同类问题
- 日志中出现的 Docker 非致命警告 `LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 5)` 不是失败原因，但也建议后续将 `ENV HTTPD_PREFIX /usr/local/apache2` 改为 `ENV HTTPD_PREFIX=/usr/local/apache2` 以消除 BuildKit 警告

## 修复验证要求
不适用（infra-error，无需修改 PR 代码）。
