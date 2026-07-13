# CI 失败分析报告

## 基本信息
- PR: #2997 — chore(cesm): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: SVN SSL证书不匹配
- 新模式症状关键词: svn, E230001, Server SSL certificate verification failed, certificate issued for a different hostname

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
- 失败原因: CESM 的 `checkout_externals` 脚本内部调用 `svn checkout` 从 `svn-ccsm-models.cgd.ucar.edu` 拉取 `chem_proc` 组件，该 SVN 服务器的 SSL 证书与当前主机名不匹配（`certificate issued for a different hostname`），导致 TLS 握手被拒，svn 无法建立连接。

### 与 PR 变更的关联
PR 变更与此失败**无关**。这是一个网络/基础设施层面的外部依赖问题——NCAR/UCAR 的 SVN 服务器 SSL 证书配置存在问题。CESM 构建流程中 `checkout_externals` 需要从外部 SVN 仓库拉取 `chem_proc` 组件，该服务器的 SSL 证书在 CI 构建环境中无法通过验证。PR 的 Dockerfile 代码本身无任何错误，此前置依赖步骤（yum 安装、mpich/hdf5/netcdf/pnetcdf 编译安装）均成功完成。

## 修复方向

### 方向 1（置信度: 高）
**问题本质**：外部 SVN 服务器 SSL 证书配置错误，非 PR 代码问题。此失败需要 CI 基础设施管理员或 NCAR/UCAR 方面处理：
- 等待 NCAR/UCAR 修复其 SVN 服务器 `svn-ccsm-models.cgd.ucar.edu` 的 SSL 证书；
- 或在 CI 构建环境中临时跳过该 SVN 服务器的 SSL 验证（不推荐，有安全风险）。

### 方向 2（置信度: 低）
如果上游服务器短期内无法修复，可在 Dockerfile 中的 `./manage_externals/checkout_externals` 之前添加 svn 配置，接受该服务器的 SSL 证书（如通过 `svn --non-interactive --trust-server-cert-failures=unknown-ca,cn-mismatch` 或 `echo p | svn info ...` 预先缓存证书），但此方案需确认 CI 安全策略是否允许。

## 需要进一步确认的点
1. 确认 `svn-ccsm-models.cgd.ucar.edu` 是否在不同时间段/不同网络环境（如从本地或 NCAR 内部网络）存在同样的 SSL 证书问题——可能是 CI 构建节点的时间/CA 根证书库过期，而非服务器端问题。
2. 确认 CESM 上游社区是否有对应的替代方案（如从 GitHub 获取 chem_proc 的镜像或预先打包版）。
3. 确认其他基于 openEuler 的 CESM 构建（如旧版 SP3 的 Dockerfile）是否也曾遇到同样问题，以及是否有已知的 workaround。

## 修复验证要求
（不适用——此为 infra-error，非 PR 代码问题，Code Fixer 无需处理。若后续确定需要 Dockerfile 层面的 workaround，则需要 code-fixer 在 CI 环境中实际验证 svn 连接是否可通过修改后的配置成功建立。）
