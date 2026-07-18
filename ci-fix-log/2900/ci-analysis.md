# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2` shell 测试框架，导致容器镜像的 [Check] 阶段无法执行任何测试用例

### 与 PR 变更的关联
本次 PR 仅新增 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套文件（httpd-foreground 启动脚本、README 更新、image-info.yml 更新、meta.yml 更新）。Docker 构建（configure + make + make install）和镜像推送均已成功完成：

- `#10 DONE 41.6s` — 源码编译安装成功
- `#11 DONE 0.1s` — 用户/组创建及配置修改成功
- `#12 DONE 0.0s` — `COPY httpd-foreground` 成功
- `#13 DONE 0.1s` — `chmod +x` 成功
- `#14 DONE 31.3s` — 镜像导出/推送成功
- `[Build] finished` / `[Push] finished` — 构建与推送阶段均正常结束

失败仅发生在构建完成后的 [Check] 测试阶段，`shunit2` 缺失是 CI 运行环境问题，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 测试框架（例如 `dnf install shunit2` 或 `yum install shunit2`），使 `eulerpublisher` 的容器镜像检查阶段能正常执行。此修复属于 CI 运维操作，无需修改 PR 中的任何代码或 Dockerfile。

## 需要进一步确认的点
- 确认 shunit2 在 openEuler 仓库中的确切包名（可能是 `shunit2` 或 `shUnit2`）
- 确认该 CI runner 的 shunit2 缺失是否影响其他 PR 的 [Check] 阶段（如属全局性问题，应将 shunit2 纳入 CI runner 标准预装清单）
