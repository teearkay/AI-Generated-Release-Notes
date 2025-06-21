# Variables
$StorageAccountName = "releasenotegeneratorappm"
$RequiredRoles = @(
    "Storage Blob Data Contributor",
    "Storage Queue Data Contributor",
    "Storage Table Data Contributor"
)

# Get the subscription ID
$SubscriptionId = (az account show --query id -o tsv)
if (-not $SubscriptionId) {
    Write-Host "Failed to retrieve subscription ID. Ensure you are logged in using 'az login'." -ForegroundColor Red
    exit 1
}
Write-Host "Subscription ID: $SubscriptionId"

# Get the resource group for the storage account
$ResourceGroup = (az storage account show --name $StorageAccountName --query resourceGroup -o tsv)
if (-not $ResourceGroup) {
    Write-Host "Failed to retrieve resource group for storage account: $StorageAccountName" -ForegroundColor Red
    exit 1
}
Write-Host "Resource Group: $ResourceGroup"

# Assign roles to "All Users" group
foreach ($Role in $RequiredRoles) {
    Write-Host "Assigning role: $Role"
    az role assignment create `
        --role $Role `
        --scope "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Storage/storageAccounts/$StorageAccountName" `
        --assignee "AllUsers"
}

Write-Host "Role assignments completed successfully." -ForegroundColor Green