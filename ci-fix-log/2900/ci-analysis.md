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
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI Runner 的 `eulerpublisher` 测试框架中 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段在执行容器检查测试时，`common_funs.sh` 第 13 行尝试 `source shunit2` 加载 shell 单元测试框架，但 CI runner 上未安装 `shunit2`，导致测试脚本无法启动，所有检查项均未执行。

### 与 PR 变更的关联
PR 变更与失败**无关**。Docker 构建（configure → make → make install）全部成功，镜像构建并推送完成（`#14 DONE 31.3s`）。失败发生在 `eulerpublisher` 框架的容器检查（[Check]）阶段，属于 CI runner 基础设施问题——测试运行器缺少 `shunit2` 这个 shell 测试框架包。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 包。对于 openEuler 系统，可通过 `yum install shunit2` 安装，或手动将 `shunit2` 脚本放置到 PATH 可见路径下（如 `/usr/local/bin/`）。安装后重新触发 CI 流水线即可。

## 需要进一步确认的点
- 确认同一 CI runner 上的其他镜像 PR 的 [Check] 阶段是否也出现同样的 `shunit2: file not found` 错误。如果是，说明该 runner 的构建环境中缺失 `shunit2` 是全局性问题，非本 PR 独有。
- 如仅有本 PR 出现此错误，需确认 runner 环境是否最近变更（如重建镜像时遗漏了 `shunit2` 包的安装步骤）。
