# CI 失败分析报告

## 基本信息
- PR: #2997 — chore(cesm): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: SVN SSL证书不匹配
- 新模式症状关键词: svn, E230001, SSL certificate verification failed, certificate issued for a different hostname

## 根因分析

### 直接错误
```
#16 90.96 Checking out externals: chem_proc, ERROR:root:Command '['svn', 'checkout', '--quiet', 'https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04', '/opt/ncar/cesm2/components/cam/chem_proc']' returned non-zero exit status 1.
#16 92.39 ERROR:root:Failed with output:
#16 92.39     svn: E170013: Unable to connect to a repository at URL 'https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04'
#16 92.39     svn: E230001: Server SSL certificate verification failed: certificate issued for a different hostname
```

### 根因定位
- 失败位置: `HPC/cesm/2.2.2/24.03-lts-sp4/Dockerfile:52-55`（`./manage_externals/checkout_externals` 步骤）
- 失败原因: CESM 构建过程中 `manage_externals/checkout_externals` 脚本尝试通过 `svn checkout` 从 `svn-ccsm-models.cgd.ucar.edu` 拉取 `chem_proc` 子组件（`chem_proc5_0_04`），但该 SVN 服务器的 SSL 证书的 CN/SAN 与实际主机名 `svn-ccsm-models.cgd.ucar.edu` 不匹配，导致 HTTPS 连接被拒绝。

### 与 PR 变更的关联
PR 新增了 CESM 2.2.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套的 `config_compilers.xml`。这是全新文件，其构建流程完整遵循 CESM 官方的 `manage_externals/checkout_externals` 外部依赖管理脚本。该脚本在检出子组件时依赖 SVN 协议访问 UCAR 的 SVN 仓库，而该仓库的 SSL 证书存在配置问题。此失败与 PR 代码本身无关，属于上游基础设施问题。

## 修复方向

### 方向 1——跳过 SVN SSL 验证（置信度: 中）
在 Dockerfile 的 `./manage_externals/checkout_externals` 之前，配置 subversion 客户端以接受不受信任的 SSL 证书。通过设置 `~/.subversion/servers` 文件或传递 `--trust-server-cert-failures` 参数。

具体操作：在 `RUN` 指令中，先执行 `svn --non-interactive --trust-server-cert-failures=cn-mismatch ls https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04` 预先接受该证书（此操作会将证书缓存到 `~/.subversion/auth/`），之后 `./manage_externals/checkout_externals` 即可正常执行。

### 方向 2——替换 SVN 源为 Git 镜像（置信度: 低）
如果 `chem_proc` 组件的上游在 GitHub 或其他 Git 平台有镜像，可以将 `manage_externals/checkout_externals` 的 Externals 配置从 SVN 替换为 Git 源。但 CESM 的 `Externals_CAM.cfg` 中 `chem_proc` 条目的 `repo_url` 指向 SVN 是上游硬编码的，修改需要 patch 管理脚本，复杂度较高。

## 需要进一步确认的点
1. **SVN 服务器证书是否永久性问题**：需确认 `svn-ccsm-models.cgd.ucar.edu` 的 SSL 证书是否为永久性配置错误，还是临时性的证书更新过渡期问题。如果是临时问题，可直接重试构建；如果长期存在，则需要上述修复方向。
2. **CESM 上游是否已有 Git 替代方案**：确认 `chem_proc` 组件在 GitHub（如 `ESCOMP` 或 `NCAR` 组织下）是否有官方 Git 仓库替代 SVN。
3. **其他使用 CESM 的 Dockerfile 是否也受影响**：检查仓库中已有的其他 CESM Dockerfile（如有）是否也遇到同样的 SVN 问题，以确认这是否是 CI 环境中首次触发。

## 修复验证要求
若采用方向 1，code-fixer 需验证：
1. 修改后的 Dockerfile 在构建时能正常通过 `svn checkout` 步骤，`chem_proc` 被成功检出到 `/opt/ncar/cesm2/components/cam/chem_proc`
2. 构建完成的镜像中 CESM 的外部依赖目录完整性正确（所有 `manage_externals` 子组件均存在）
3. `~/.subversion/auth/` 中的缓存证书不会泄露到最终镜像层（在同一个 RUN 层内执行 svn 操作并清理证书缓存）
