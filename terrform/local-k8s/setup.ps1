$ErrorActionPreference = 'Stop'

function Get-Platform {
  if ($PSVersionTable.PSEdition -eq 'Desktop' -or $env:OS -eq 'Windows_NT') { return 'windows' }
  if ($IsMacOS) { return 'macos' }
  if ($IsLinux) { return 'linux' }
  return 'unknown'
}

function Install-ToolIfMissing($name, $command, $wingetId, $manualHint) {
  if (Get-Command $command -ErrorAction SilentlyContinue) {
    return
  }

  $platform = Get-Platform
  Write-Warning "$name ($command) not found."

  if ($platform -eq 'windows' -and $wingetId -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "Attempting to install $name via winget..." -ForegroundColor Yellow
    winget install -e --id $wingetId --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'User')
  }

  if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
    throw "Missing required tool: $name ($command). $manualHint"
  }
}

function Require-MinVersion($name, $actual, $minimum) {
  try {
    $actualVersion = [version]$actual
    $minimumVersion = [version]$minimum
  }
  catch {
    throw "Unable to parse $name version. Actual: $actual"
  }

  if ($actualVersion -lt $minimumVersion) {
    throw "$name version $actualVersion is below required minimum $minimumVersion"
  }
}

Write-Host 'Setting up local-k8s prerequisites...' -ForegroundColor Cyan

Install-ToolIfMissing 'Terraform' 'terraform' 'Hashicorp.Terraform' 'Install Terraform from https://developer.hashicorp.com/terraform/install'
Install-ToolIfMissing 'kubectl' 'kubectl' 'Kubernetes.kubectl' 'Install kubectl from https://kubernetes.io/docs/tasks/tools/'
Install-ToolIfMissing 'Docker Desktop' 'docker' 'Docker.DockerDesktop' 'Install Docker Desktop from https://www.docker.com/products/docker-desktop/'
Install-ToolIfMissing 'Google Cloud SDK' 'gcloud' 'Google.CloudSDK' 'Install gcloud from https://cloud.google.com/sdk/docs/install'

$terraformVersion = (terraform version -json | ConvertFrom-Json).terraform_version
Require-MinVersion 'Terraform' $terraformVersion '1.6.0'

$kubectlVersion = ((kubectl version --client -o json | ConvertFrom-Json).clientVersion.gitVersion).TrimStart('v')
Require-MinVersion 'kubectl' $kubectlVersion '1.29.0'

$dockerVersion = (docker version --format '{{.Client.Version}}').Trim()
Require-MinVersion 'Docker CLI' $dockerVersion '24.0.0'

$gcloudVersion = ((gcloud version --format=json | ConvertFrom-Json).'Google Cloud SDK').Trim()
Require-MinVersion 'Google Cloud SDK' $gcloudVersion '450.0.0'

$ctx = kubectl config current-context
if ($ctx -ne 'docker-desktop') {
  throw "Expected docker-desktop context for local-k8s. Current context: $ctx"
}

$acct = gcloud auth list --filter=status:ACTIVE --format='value(account)'
if (-not $acct) {
  throw 'No active gcloud account found. Run: gcloud auth login'
}

docker version | Out-Null
terraform init
Write-Host 'local-k8s prerequisites and minimum versions look good.' -ForegroundColor Green
