# 修复摘要

## 修复的问题
修正 Dockerfile 中两处 UndefinedVar lint 警告（`$CPATH` 自引用和 `${daospath}` 未定义）。

## 修改的文件
- `Storage/daos/2.6.3/24.03-lts-sp4/Dockerfile`: 修正 line 31 和 line 32 的 ENV 变量引用

## 修复逻辑
1. **line 31**: `ENV CPATH=/daos/install/include/:$CPATH` → `ENV CPATH=/daos/install/include/:${CPATH:-}`
   - 将 `$CPATH` 自引用改为 `${CPATH:-}`，当 CPATH 未定义时默认使用空字符串，避免 UndefinedVar 警告。
2. **line 32**: `ENV PATH=/daos/install/bin/:${daospath}/install/sbin:$PATH` → `ENV PATH=/daos/install/bin/:/daos/install/sbin:$PATH`
   - `${daospath}` 变量从未定义，根据 WORKDIR `/daos` 和上下文推断其预期值为 `/daos`，直接使用字面路径。

## 关于构建失败 (HTTP 429)
CI 分析报告明确将此构建失败归类为 `infra-error`（GitHub Raw 限流），属于 CI 基础设施层面的网络问题，与 PR 代码变更无因果关联。DAOS scons 构建过程中从 `raw.githubusercontent.com` 下载 mercury 补丁时触发 GitHub 速率限制（HTTP 429），此类问题无法通过修改 Dockerfile 代码解决，需 CI 运维层面处理（如配置 GitHub token 认证或设置 HTTP 代理缓存）。

## 潜在风险
- line 32 将 `${daospath}` 替换为 `/daos` 基于上下文推断（WORKDIR=/daos），若原意是其他路径则需调整。但从语义和 DAOS 安装目录结构来看，`/daos` 是正确的路径。