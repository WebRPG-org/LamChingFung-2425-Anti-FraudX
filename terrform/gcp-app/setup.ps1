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

Write-Host 'Setting up gcp-app prerequisites...' -ForegroundColor Cyan

Install-ToolIfMissing 'Terraform' 'terraform' 'Hashicorp.Terraform' 'Install Terraform from https://developer.hashicorp.com/terraform/install'
Install-ToolIfMissing 'kubectl' 'kubectl' 'Kubernetes.kubectl' 'Install kubectl from https://kubernetes.io/docs/tasks/tools/'
Install-ToolIfMissing 'Google Cloud SDK' 'gcloud' 'Google.CloudSDK' 'Install gcloud from https://cloud.google.com/sdk/docs/install'

$terraformVersion = (terraform version -json | ConvertFrom-Json).terraform_version
Require-MinVersion 'Terraform' $terraformVersion '1.6.0'

$kubectlVersion = ((kubectl version --client -o json | ConvertFrom-Json).clientVersion.gitVersion).TrimStart('v')
Require-MinVersion 'kubectl' $kubectlVersion '1.29.0'

$gcloudVersion = ((gcloud version --format=json | ConvertFrom-Json).'Google Cloud SDK').Trim()
Require-MinVersion 'Google Cloud SDK' $gcloudVersion '450.0.0'

$ctx = kubectl config current-context
if (-not $ctx.StartsWith('gke_')) {
  throw "Expected an active GKE context for gcp-app. Current context: $ctx"
}

kubectl get crd managedcertificates.networking.gke.io | Out-Null

$acct = gcloud auth list --filter=status:ACTIVE --format='value(account)'
if (-not $acct) {
  throw 'No active gcloud account found. Run: gcloud auth login'
}

terraform init
Write-Host 'gcp-app prerequisites and minimum versions look good.' -ForegroundColor Green
