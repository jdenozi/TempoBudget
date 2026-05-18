# N8N Workflow Sync

Synchronize local n8n workflow templates with the n8n instance.

## Context

The project has n8n workflow templates in `/home/debian/TempoBudget/n8n-workflows/`:
- `pro-invoice-email.json` - Send Pro invoices to clients
- `payment-reminder.json` - Payment reminder emails
- `payment-confirmation.json` - Payment confirmation emails
- `stripe-invoice.json` - Stripe invoice emails

## Instructions

When the user invokes this skill:

1. **List available workflows** in the `n8n-workflows/` directory

2. **Check n8n connectivity** by calling the n8n API:
   ```bash
   curl -s -X GET "${N8N_URL}/api/v1/workflows" \
     -H "X-N8N-API-KEY: ${N8N_API_KEY}" | jq '.data | length'
   ```

3. **For each workflow to sync**:
   - Read the local JSON file
   - Check if a workflow with the same name exists in n8n
   - If exists: UPDATE via `PUT /api/v1/workflows/{id}`
   - If not exists: CREATE via `POST /api/v1/workflows`

4. **Activate the workflow** after import if it was active before

## Environment Variables Required

- `N8N_URL` - Base URL of the n8n instance (e.g., `https://n8n.tempo-finance.com`)
- `N8N_API_KEY` - API key for n8n authentication

## Usage Examples

- `/n8n-sync` - Sync all workflows
- `/n8n-sync pro-invoice` - Sync only the pro-invoice workflow
- `/n8n-sync --list` - Just list workflows without syncing

## API Reference

### List workflows
```
GET /api/v1/workflows
```

### Create workflow
```
POST /api/v1/workflows
Content-Type: application/json
Body: { workflow JSON }
```

### Update workflow
```
PUT /api/v1/workflows/{id}
Content-Type: application/json
Body: { workflow JSON }
```

### Activate workflow
```
POST /api/v1/workflows/{id}/activate
```

## Error Handling

- If n8n is not reachable, show connection error and suggest checking N8N_URL
- If API key is invalid, show auth error and suggest checking N8N_API_KEY
- If workflow import fails, show the specific error from n8n
