# Release Notes Generation - Automated Deployment Guide

Transform your Azure DevOps work items into professional release notes automatically using AI-powered Logic Apps.

## 🎯 What This Does

This solution automatically:
- 📋 Fetches work items from Azure DevOps queries  
- 🤖 Generates professional release notes using AI
- 📝 Saves formatted markdown files to SharePoint
- 📧 Sends email notifications to your team once done

## 🏁 Quick Start (5 Minutes)

### Prerequisites Checklist
- ✅ Azure subscription with Contributor role
- ✅ Azure DevOps organization access
- ✅ SharePoint Online site access  
- ✅ Office 365 Outlook access

### � Files You'll Need
- `template.json` - ARM template (ready to use)
- `parameters.json` - Copy `parameters.example.json` and edit with your configuration

---

## 📋 Step 1: Prepare Your Configuration

### Copy the Parameters Template
```bash
cp parameters.example.json parameters.json
```

### 🔧 Configuration

Edit `parameters.json` with **your specific values**:

| Parameter | What to Put Here | Where to Find It |
|-----------|------------------|------------------|
| `devOpsOrganization` | Your DevOps org name | Query URL |
| `devOpsProject` | Your project name | Query URL |
| `emailRecipients` | Email addresses (semicolon separated) | Your team email list |
| `sharePointSiteUrl` | Full SharePoint site URL | SharePoint address bar |
| `sharePointFolderPath` | Folder path for output files | SharePoint document library path |

**Example Query URL**: `https://{devOpsOrganization}.visualstudio.com/{devOpsProject}/_queries/query-edit/{QueryId}/`

**Finding Configuration Values**

| Need | Location | URL Pattern |
|------|----------|-------------|
| DevOps Organization | DevOps home page | `https://{ORG}.visualstudio.com/` |
| DevOps Project | Project page | `https://{ORG}.visualstudio.com/{PROJECT}/` |
| Work Item Query ID | Query editor URL | `.../_queries/query-edit/{QUERY-ID}/` |
| SharePoint Site URL | Site address bar | `https://{company}.sharepoint.com/sites/{site}` |

#### 🧠 AI Configuration

| Parameter | Purpose | Required? | Notes |
|-----------|---------|-----------|--------|
| `singleWorkItemSemanticConfig` | AI analysis of individual work items | ⚠️ **Required** | Recommended to onboard with your product-specific documentation to provide better context for work item analysis. |
| `finalReleaseNotesSemanticConfig` | Final release notes formatting style | ✅ **Optional** | Default format works well for most teams. Custom formatting available to use your own templates. |

**Custom Configurations**: We can create semantic configurations tailored to your:
- **Product documentation** for more accurate work item analysis
- **Release note formatting** preferences and style guides
- **[WIP] Team-specific** terminology and communication standards (Glossary)

> 💡 **Need custom configurations?** Contact our team with your requirements: tkishnani@microsoft.com, bkhetharpal@microsoft.com, clafernandes@microsoft.com

---

## 🚀 Step 2: Deploy to Azure

### Option A: Azure CLI
```bash
# Login and set subscription
az login
az account set --subscription "your-subscription-id"

# Create resource group
az group create --name "your-resource-group-name" --location "azure-region"

# Deploy template
az deployment group create \
  --resource-group "your-resource-group-name" \
  --template-file template.json \
  --parameters parameters.json
```

### Option B: PowerShell
```powershell
# Login and set subscription
Connect-AzAccount
Set-AzContext -SubscriptionId "your-subscription-id"

# Create resource group  
New-AzResourceGroup -Name "your-resource-group-name" -Location "azure-region"

# Deploy template
New-AzResourceGroupDeployment `
  -ResourceGroupName "your-resource-group-name" `
  -TemplateFile "template.json" `
  -TemplateParameterFile "parameters.json"
```
---

## 🏗️ What Gets Created

- **Logic App Workflow**: Orchestrates the entire process
- **API Connections**: Secure connections to DevOps, Office 365, SharePoint
- **Managed Identity**: For secure Azure resource access

## � How It Works

```
DevOps Query → Work Items → AI Processing → Release Notes → SharePoint + Email
```

1. **Trigger**: Manual or scheduled execution
2. **Fetch**: Gets work items from your DevOps query  
3. **Clean**: Processes HTML content and comments
4. **Generate**: AI creates professional release notes
5. **Deliver**: Saves to SharePoint and emails your team

---

---

## ⚙️ Step 3: Complete Setup (Critical!)

### 3A. Authenticate Connections
🚨 **This step is required** - the Logic App won't work without it.

1. **Azure Portal** → **Your Resource Group** → **API connections**
2. Click each connection and authenticate:
   - **visualstudioteamservices-2** ➜ Sign in with DevOps access
   - **office365** ➜ Sign in with Outlook access  
   - **sharepointonline** ➜ Sign in with SharePoint access

> ⚠️ **If authentication fails**: Go to **Logic App Designer** and click on any action showing a connection error, then select **"Add new connection"** to create fresh connections with your credentials.

---

## 🎉 Step 4: Run Your Logic App

### 4A. Configure Runtime Parameters
1. **Azure Portal** → **Your Resource Group** → **Logic App** → **Logic app designer**
2. At the top, find **Parameters** section
3. **Set these values** (required for each run):
   - **OutputFileName**: Your release file name (e.g., "Sprint-42-Release")
   - **WorkItemQuery**: Your DevOps Work Item Query GUID

#### 🔍 Finding Your Work Item Query ID
1. Go to **Azure DevOps** → **Your Project** → **Boards** → **Queries**  
2. Open your query → Look at URL: `https://contoso.visualstudio.com/ProductDev/_queries/query-edit/12345678-abcd-1234-abcd-123456789abc/`
3. Copy the GUID (**12345678-abcd-1234-abcd-123456789abc**) and paste into **WorkItemQuery** parameter

### 4B. Execute and Monitor
1. **Logic App Designer** → **Run**
2. Check **Run History** for success/errors
3. Verify files appear in your SharePoint folder
4. Check your email for notifications

> ⏱️ **Processing Time**: Allow 30-60 seconds per work item in the query.

## 🛠️ Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| **"Connection not authenticated"** | Go to API connections in portal and re-authenticate OR Create a new connection. |
| **"Work items not found"** | Verify your WorkItemQuery GUID is correct |
| **"Permission denied"** | Check your permissions to DevOps/SharePoint/Outlook |
| **Logic App fails** | Check Run History for detailed error messages |

### 🆘 Need Help?
**Support Team**: tkishnani@microsoft.com, bkhetharpal@microsoft.com, clafernandes@microsoft.com

---