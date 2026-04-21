$ErrorActionPreference = 'Stop'

function Get-Platform {
  if ($PSVersionTable.PSEdition -eq 'Desktop' -or $env:OS -eq 'Windows_NT') { return 'windows' }
  if ($IsMacOS) { return 'macos' }
  if ($IsLinux) { return 'linux' }
  return 'unknown'
}

function Install-ToolIfMissing($name, $command, $wingetId, $manualHint) {
  if (Get-Command $command -ErrorAction SilentlyContinue) { return }
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

Write-Host 'Setting up azure-infra prerequisites...' -ForegroundColor Cyan
Install-ToolIfMissing 'Terraform' 'terraform' 'Hashicorp.Terraform' 'Install Terraform from https://developer.hashicorp.com/terraform/install'
Install-ToolIfMissing 'Azure CLI' 'az' 'Microsoft.AzureCLI' 'Install Azure CLI from https://learn.microsoft.com/cli/azure/install-azure-cli'
az account show --output none
terraform init
Write-Host 'azure-infra prerequisites look good.' -ForegroundColor Green
