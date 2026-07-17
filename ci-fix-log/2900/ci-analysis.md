# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

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
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行环境中未安装 `shunit2`（Shell 单元测试框架），导致 [Check] 阶段的测试脚本 `common_funs.sh` 在试图加载 `shunit2` 库时失败。Check 表中无任何检查项被填充，证明测试框架在初始化阶段就已崩溃。

### 与 PR 变更的关联
该失败与 PR 变更**无关**。PR 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 平台上的 Dockerfile、httpd-foreground 脚本及配套元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像构建（#10~#13）、导出和推送全部成功完成：

- `#10 DONE 41.6s` — configure + make + make install 成功
- `#11 DONE 0.1s` — groupadd/useradd 配置成功
- `#12 DONE 0.0s` — COPY httpd-foreground 成功
- `#13 DONE 0.1s` — chmod 成功
- `#14 DONE 31.3s` — 镜像导出和推送成功

失败发生在构建流程之后的 [Check] 阶段，根因是 CI runner 环境缺少 `shunit2` 依赖，与 Dockerfile 或任何代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI 运行环境中安装 `shunit2` 包。openEuler 上可通过 `dnf install shunit2 -y` 安装。若 CI 环境使用 pip 管理工具依赖，也可考虑 `pip install shunit2` 或将 `shunit2` 纳入环境初始化脚本的依赖列表。

### 方向 2（置信度: 低）
若 CI 基础设施不便修改，可考虑在 Check 脚本阶段前增加预检查步骤，先判断 `shunit2` 是否可用，若不可用则跳过测试并输出警告而非直接失败。但此方向仅作为临时绕过方案，不推荐。

## 需要进一步确认的点
- 确认 CI runner 镜像中是否预装了 `shunit2` 包，或确认部署该 runner 的环境配置模版是否遗漏了该依赖。
- 查看同类成功 PR（如 httpd 2.4.66-oe2403sp2）的 [Check] 阶段日志，对比确认是否为本次构建环境独有问题。
