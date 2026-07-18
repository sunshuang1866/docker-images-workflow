# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: `shunit2: No such file or directory`, `common_funs.sh`, `[Check] test failed`

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 的 `[Check]` 测试阶段依赖 `shunit2` 测试框架，但该框架未安装或不在 PATH 中，导致容器功能验证无法执行

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh，并更新了 README.md 和 meta.yml。Docker 构建和推送阶段均成功完成：

- `#8 DONE 268.4s` — PostgreSQL 源码编译安装完成，所有 `make install` 步骤正常
- `#9 [3/4] COPY entrypoint.sh` — DONE
- `#10 [4/4] RUN chmod 755` — DONE
- `#11 exporting to image` — 镜像导出成功，sha256: a988378e…
- `#12 [auth]` — 认证通过
- `[Build] finished` / `[Push] finished` — 构建和推送均成功

失败仅发生在构建/推送完成后的 `[Check]` 容器功能测试阶段，原因是 CI 运行环境中缺失 `shunit2` 测试框架，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是一个纯 Bash 的 xUnit 测试框架，通常安装方式为：
```
# 方式一：通过包管理器
dnf install -y shunit2

# 方式二：直接下载
wget -O /usr/local/bin/shunit2 https://...  # 从 shunit2 GitHub release 获取
chmod +x /usr/local/bin/shunit2
```
这是 CI 基础设施维护任务，**Code Fixer 无需修改 Dockerfile 或任何 PR 文件**。

## 需要进一步确认的点
- 确认 CI runner 节点上 `shunit2` 是否确实未安装，或是否仅为 PATH 配置问题
- 确认同一节点上其他 PR（非 SP4 镜像）的 `[Check]` 测试是否能正常运行，以排除节点级故障
- 确认 `shunit2` 在 CI runner 的标配软件列表中的安装策略
