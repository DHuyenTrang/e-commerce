$ErrorActionPreference = "Stop"

$sqlDir = Join-Path $PSScriptRoot "mock_data\sql"
$containerName = "ecom_postgres"
$containerDir = "/tmp/mock_data_sql"

if (-not (Test-Path $sqlDir)) {
  throw "SQL mock data directory not found: $sqlDir"
}

$dbScripts = @(
  @{ Database = "gateway_db"; Files = @("common_django.sql") },
  @{ Database = "user_db"; Files = @("common_django.sql", "user_service.sql") },
  @{ Database = "staff_db"; Files = @("common_django.sql", "staff_service.sql") },
  @{ Database = "product_db"; Files = @("common_django.sql", "product_service.sql") },
  @{ Database = "cart_db"; Files = @("common_django.sql", "cart_service.sql") },
  @{ Database = "order_db"; Files = @("common_django.sql") },
  @{ Database = "payment_db"; Files = @("common_django.sql", "payment_service.sql") },
  @{ Database = "shipping_db"; Files = @("common_django.sql", "shipping_service.sql") },
  @{ Database = "comment_db"; Files = @("common_django.sql", "comment_service.sql") }
)

Write-Host "==> Copying SQL files into $containerName"
docker exec $containerName rm -rf $containerDir
docker exec $containerName mkdir -p $containerDir
docker cp "$sqlDir\." "${containerName}:$containerDir"

foreach ($entry in $dbScripts) {
  foreach ($file in $entry.Files) {
    $hostFile = Join-Path $sqlDir $file
    if (-not (Test-Path $hostFile)) {
      throw "SQL file not found: $hostFile"
    }

    Write-Host "==> $($entry.Database): $file"
    docker exec -i $containerName psql -U root -d $entry.Database -v ON_ERROR_STOP=1 -f "$containerDir/$file"
  }
}

Write-Host "SQL mock data import completed."
