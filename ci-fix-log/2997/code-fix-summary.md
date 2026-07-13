# 修复摘要

## 修复的问题
CESM 2.2.2 构建过程中 `checkout_externals` 步骤因 SVN 服务器证书主机名不匹配（`E230001: certificate issued for a different hostname`）而失败。

## 修改的文件
- `HPC/cesm/2.2.2/24.03-lts-sp4/Dockerfile`: 在第 54 行的 `printf` 命令中追加 `trust-server-cert-failures = unknown-ca,cn-mismatch,expired,not-yet-valid,other`，使 SVN 客户端（1.14.3）忽略证书主机名不匹配错误。

## 修复逻辑
分析报告指出根因是 `svn-ccsm-models.cgd.ucar.edu` 的 TLS 证书与访问主机名不匹配，原有的 `ssl-trust-default-ca = yes` 只能解决 CA 信任链问题，无法解决主机名不匹配。`trust-server-cert-failures` 是 SVN 1.9+ 提供的细粒度证书错误忽略选项，通过添加 `cn-mismatch` 可覆盖主机名不匹配场景。openEuler 24.03-LTS-SP4 中安装的 subversion 版本为 1.14.3，满足此选项的最低版本要求。

## 潜在风险
- 该修复降低了 SVN 客户端对上游服务器证书的验证强度（允许主机名不匹配、过期证书等），如果上游 SVN 服务器证书存在恶意篡改，此配置将无法检测到中间人攻击。
- 如果上游 SVN 服务器的证书问题已修复，此配置将不再必要但不影响构建（多余的容忍不会破坏正常流程）。
- 该修改仅影响当前 Dockerfile 的构建过程，不影响其他镜像或组件。