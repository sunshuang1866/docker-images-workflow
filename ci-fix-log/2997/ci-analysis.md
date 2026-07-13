# CI 失败分析报告

## 基本信息
- PR: #2997 — chore(cesm): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: SVN SSL证书不匹配
- 新模式症状关键词: svn, E230001, Server SSL certificate verification failed, certificate issued for a different hostname, checkout_externals

## 根因分析

### 直接错误
```
#16 90.96 Checking out externals: chem_proc, ERROR:root:Command '['svn', 'checkout', '--quiet', 'https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04', '/opt/ncar/cesm2/components/cam/chem_proc']' returned non-zero exit status 1.
#16 92.39 ERROR:root:Failed with output:
#16 92.39     svn: E170013: Unable to connect to a repository at URL 'https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04'
#16 92.39     svn: E230001: Server SSL certificate verification failed: certificate issued for a different hostname
#16 ERROR: process "/bin/sh -c yum install -y subversion cmake lapack-devel blas-devel perl-XML-LibXML &&     git clone -b release-cesm${VERSION} https://github.com/ESCOMP/cesm.git cesm2 &&     cd cesm2 &&     ./manage_externals/checkout_externals" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile 第52-55行（`RUN` 步骤中的 `./manage_externals/checkout_externals`）
- 失败原因: CESM 的 `checkout_externals` 脚本在 checkout `chem_proc` 子模块时，通过 SVN 访问 `svn-ccsm-models.cgd.ucar.edu`，该服务器的 SSL 证书与主机名不匹配（`E230001: certificate issued for a different hostname`），导致 SVN checkout 失败，整个 Docker 构建中止。

### 与 PR 变更的关联
**直接关联。** 本次 PR 新增了完整的 `HPC/cesm/2.2.2/24.03-lts-sp4/Dockerfile`，在该 Dockerfile 的构建步骤（step 10/13）中执行 `./manage_externals/checkout_externals` 时触发了上游 SVN 服务器的 SSL 证书问题。这不是 Dockerfile 本身写法有误，而是上游 NCAR/UCAR 的 SVN 基础设施（`svn-ccsm-models.cgd.ucar.edu`）存在证书配置问题。CESM 主仓库已迁移至 GitHub，但其 `Externals.cfg`（由 `checkout_externals` 读取）中 `chem_proc` 组件仍指向旧 SVN 服务器。

## 修复方向

### 方向 1（置信度: 中）
在 Dockerfile 的 `./manage_externals/checkout_externals` 执行前，通过环境变量或 SVN 全局配置允许证书信任异常（`--trust-server-cert-failures`），使 SVN checkout 忽略 SSL 主机名不匹配错误。需确认 openEuler 24.03-LTS-SP4 中 svn 1.14.x 版本对该选项的支持情况。

### 方向 2（置信度: 低）
检查 `chem_proc5_0_04` 是否已有 Git 镜像（如 ESCOMP 组织的 GitHub 仓库），若是，则在 Dockerfile 中修改 CESM 的 `Externals.cfg`（`Externals_CAM.cfg`）将 `chem_proc` 的拉取方式从 `svn` 改为 `git`，指向 GitHub 镜像仓库。

### 方向 3（置信度: 低）
在 `./manage_externals/checkout_externals` 执行前，用 `sed` 临时修改 External 配置文件中 `chem_proc` 的 `repo_url`，将 `https://svn-ccsm-models.cgd.ucar.edu/tools/proc_atm/chem_proc/release_tags/chem_proc5_0_04` 替换为一个可用的镜像源。

## 需要进一步确认的点
- `svn-ccsm-models.cgd.ucar.edu` 的 SSL 证书问题是否为临时故障还是长期问题，需通过外部手段验证该 SVN 服务器当前是否仍提供服务
- `chem_proc5_0_04` 是否已托管在 ESCOMP 或其他 GitHub 组织下，如有，其准确的 Git URL 和分支/tag 是什么
- openEuler 24.03-LTS-SP4 中 `subversion` 包的 1.14.3 版本是否支持 `--trust-server-cert-failures` 选项
- CESM 的同类别 Dockerfile（如 `22.03-lts-sp3`、`24.03-lts-sp3` 版本）是否已遇到过同样问题，如已有修复方案可参考

## 修复验证要求
无论采用哪个修复方向，code-fixer 必须：
1. 在修改 Dockerfile 后触发完整的 Docker 构建，确认 `checkout_externals` 步骤（特别是 `chem_proc` 的 checkout）能成功通过
2. 若采用方向2/3修改 External 配置，需验证修改后的 URL 确实能获取到 `chem_proc5_0_04` 的完整源码，确保 CESM 后续编译不受影响
