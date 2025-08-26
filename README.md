# Bexio MCP Server Demo

![Bexio MCP Server Demo](assets/Bexio-MCP-Server-Demo.gif)

MCP server for Bexio ERP integration - enables AI assistants to interact with Bexio business management software.

**Available in [FlowHunt.io](https://flowhunt.io)** - Test this MCP server directly in FlowHunt's no-code AI automation platform with visual drag-and-drop workflow builder.

## Features

- 🔍 **Contact Management**: Search, create, update, and manage contacts
- 📄 **Invoice Operations**: Create, search, and manage invoices
- 💰 **Quote Management**: Handle quotes and proposals
- 🏗️ **Project Management**: Create and track projects
- 📦 **Item/Article Management**: Manage products and services
- 🔐 **Secure Authentication**: Uses Bexio Personal Access Tokens (PAT)
- ✅ **Smart Field Validation**: Automatic field completion and 422 error prevention
- 🛡️ **Enhanced Error Handling**: Clear guidance for missing or invalid fields

## Installation

### Prerequisites
- Python 3.10+
- Bexio account with API access

### Install
- For users:
```bash
pip install .
```
- For development (with tests and linters):
```bash
pip install -e ".[dev]"
```

## Configuration

### Getting Your Bexio Access Token

The easiest way to get an access token is using **Personal Access Tokens (PAT)**:

1. Visit [https://developer.bexio.com/pat](https://developer.bexio.com/pat)
2. Create a new Personal Access Token
3. Copy the token (it will look like: `eyJraWQiOiI2ZGM2YmJlOC1iMjZjLTExZTgtOGUwZC0w...`)

**PAT Benefits:**
- ✅ Full access to your company's data
- ✅ Valid for 6 months
- ✅ No OAuth setup required
- ✅ Perfect for personal/development use

### Alternative Authentication

If you need custom scopes or multi-user access beyond Personal Access Tokens (PAT), implement an OAuth flow in your own application using Bexio's OAuth documentation.

### Environment Setup

Create a `.env` file in your project directory:

```bash
BEXIO_ACCESS_TOKEN=your_personal_access_token_here
BEXIO_API_URL=https://api.bexio.com/2.0
BEXIO_TIMEOUT=120
```

## Usage with Claude Desktop

Add the following to your Claude Desktop configuration file:

### macOS
`~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows
`%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bexio": {
      "command": "python",
      "args": ["-m", "mcp_server_bexio.server"],
      "cwd": "/path/to/your/bexio-mcp-server",
      "env": {
        "BEXIO_ACCESS_TOKEN": "YOUR_NEW_PAT_TOKEN_HERE"
      }
    }
  }
}
```

**Important:** Replace `YOUR_NEW_PAT_TOKEN_HERE` with your actual Personal Access Token from https://developer.bexio.com/pat

## Available Tools

### Contact Management

#### search_contacts
Search for contacts using criteria.
Parameters:
- `criteria` (required): Array of search criteria objects with field/value/criteria
- `limit`: Maximum number of results (auto-filled: 50)
- `offset`: Number of records to skip (auto-filled: 0)

Example prompts:
- "Find all contacts with email containing 'gmail.com'"
- "Search for companies in Zurich"
- "Show me contacts created this month"

#### get_contact
Get detailed information about a specific contact.
Parameters:
- `contact_id` (required): Contact ID

#### create_contact
Create a new contact.
Required fields:
- `name_1`: First name or company name
Auto-filled fields (can be overridden):
- `contact_type_id`: Contact type (default: 2 for person)
- `user_id`: User ID (default: 1)
- `owner_id`: Owner ID (default: 1)

#### update_contact
Update an existing contact.
Required fields:
- `contact_id`: Contact ID
Auto-retrieved fields:
- `name_1`, `contact_type_id`, `user_id`, `owner_id`, `nr`: Retrieved from existing contact

#### list_contacts
List all contacts with optional filtering.
Parameters:
- `limit`: Maximum number of results (auto-filled: 50)
- `offset`: Number of records to skip (auto-filled: 0)
- `order_by`: Field to order by (optional)

### Invoice Management

#### search_invoices
Search for invoices using criteria.
Parameters:
- `criteria` (required): Array of search criteria objects with field/value/criteria
- `limit`: Maximum number of results (auto-filled: 50)
- `offset`: Number of records to skip (auto-filled: 0)

#### get_invoice
Get detailed information about a specific invoice.
Parameters:
- `invoice_id` (required): Invoice ID

#### create_invoice
Create a new invoice.
Required fields:
- `contact_id`: Contact ID for the invoice
- `positions`: Array with line items (each needs `text` description)
Auto-filled fields (can be overridden):
- `user_id`: User ID (default: 1)
- `nr`: Invoice number (API auto-generates)
- Position fields: `type`, `amount`, `unit_price`, `tax_id` (default: Tax ID 3 - 0% rate)

Note: Uses flat schema structure for consistent UI experience.

#### list_invoices
List all invoices with optional filtering.
Parameters:
- `limit`: Maximum number of results (auto-filled: 50)
- `offset`: Number of records to skip (auto-filled: 0)
- `order_by`: Field to order by (optional)

### Quote Management

#### search_quotes
Search for quotes using criteria.
Parameters:
- `criteria` (required): Array of search criteria objects with field/value/criteria
- `limit`: Maximum number of results (auto-filled: 50)
- `offset`: Number of records to skip (auto-filled: 0)

#### get_quote
Get detailed information about a specific quote.
Parameters:
- `quote_id` (required): Quote ID

#### create_quote
Create a new quote.
Required fields:
- `contact_id`: Contact ID for the quote
Auto-filled fields (can be overridden):
- `user_id`: User ID (default: 1)
- `nr`: Quote number (API auto-generates)
- Positions: Optional but recommended, same auto-fill as invoices

Note: Uses flat schema structure for consistent UI experience.

### Project Management

#### list_projects
List all projects with optional filtering.
Parameters:
- `limit`: Maximum number of results (auto-filled: 50)
- `offset`: Number of records to skip (auto-filled: 0)
- `order_by`: Field to order by (optional)

#### get_project
Get detailed information about a specific project.
Parameters:
- `project_id` (required): Project ID

#### create_project
Create a new project.
Required fields:
- `name`: Project name
- `contact_id`: Contact ID for the project
Auto-filled fields (can be overridden):
- `user_id`: User ID (default: 1)
- `nr`: Project number (API auto-generates)
- `pr_state_id`: Project state ID (default: 1)
- `pr_project_type_id`: Project type ID (default: 1)

### Item/Article Management

#### list_items
List all items/articles with optional filtering.
Parameters:
- `limit`: Maximum number of results (auto-filled: 50)
- `offset`: Number of records to skip (auto-filled: 0)
- `order_by`: Field to order by (optional)

#### get_item
Get detailed information about a specific item.
Parameters:
- `item_id` (required): Item ID

#### create_item
Create a new item/article.
Required fields:
- `intern_name`: Internal item name
Auto-filled fields (can be overridden):
- `user_id`: User ID (default: 1)
- `nr`: Item number (API auto-generates)
- `article_type_id`: Article type ID (default: 1)
- `currency_id`: Currency ID (default: 1)
- `is_stock`: Stock item flag (default: false)
- `delivery_price`: Delivery price (default: 0)

## Common Use Cases

### Customer Management
- Search and filter customer contacts
- Create new customer records
- Update customer information
- Track customer communication history

### Sales Operations
- Create and manage quotes
- Convert quotes to orders and invoices
- Track sales pipeline
- Generate sales reports

### Project Management
- Create and track projects
- Assign projects to customers
- Monitor project progress
- Manage project timesheets

### Inventory Management
- Manage product catalog
- Track stock levels
- Update pricing information
- Handle product variations

## Security Considerations

- Store your Bexio access token securely
- Use environment variables for sensitive configuration
- Regularly rotate access tokens
- Monitor API usage and access logs
- Implement proper error handling for API failures

## Smart Field Validation

This MCP server includes intelligent field validation to prevent common 422 errors and improve user experience:

### Automatic Field Completion
- **Required fields**: Prompts users for critical missing information
- **Safe defaults**: Auto-fills non-critical fields (user_id, project states, etc.)
- **Dynamic lookups**: Retrieves existing data for updates (contact numbers, tax IDs)
- **API-aware**: Skips fields where Bexio API provides intelligent defaults

### Enhanced Error Handling
- **Pre-validation**: Catches missing fields before API calls
- **Clear guidance**: Specific error messages explaining what's needed
- **Smart tax handling**: Automatically looks up valid tax IDs from your Bexio system
- **Field-specific help**: Distinguishes between missing vs invalid field values

### Field Types
- `REQUIRED_USER_INPUT`: Critical fields requiring user input (contact names, IDs)
- `AUTO_FILL_DEFAULT`: Safe defaults (user_id=1, project_state_id=1) - **can be overridden by user**
- `AUTO_FILL_LOOKUP`: Retrieved from existing data (for updates)
- `API_HANDLED`: Fields where API provides fallback handling

### User Override Capability
**Important**: All auto-filled fields can be overridden by providing explicit values. The system only fills missing fields - if you specify a value, it will be used instead of the default.

### Detailed Field Requirements

#### Contact Functions
**create_contact**:
- **REQUIRED**: `name_1` (first name or company name)
- **AUTO-FILLED**: `contact_type_id=2`, `user_id=1`, `owner_id=1`
- **OPTIONAL**: email, phone, address, city, country_id, language_id

**update_contact**:
- **REQUIRED**: `contact_id`
- **AUTO-RETRIEVED**: `name_1`, `contact_type_id`, `user_id`, `owner_id` from existing contact
- **OPTIONAL**: All other contact fields

#### Invoice Functions
**create_invoice**:
- **REQUIRED**: `contact_id`, `positions` array
- **AUTO-FILLED**: `user_id=1`
- **POSITION REQUIREMENTS**: Each position needs `text` (description)
- **AUTO-FILLED PER POSITION**: `type='KbPositionCustom'`, `amount=1`, `unit_price=0.0`, `tax_id` (looked up)

#### Quote Functions
**create_quote**:
- **REQUIRED**: `contact_id`
- **AUTO-FILLED**: `user_id=1`
- **POSITIONS**: Optional but recommended, same auto-fill rules as invoices

#### Project Functions
**create_project**:
- **REQUIRED**: `name`, `contact_id`
- **AUTO-FILLED**: `user_id=1`, `pr_state_id=1`, `pr_project_type_id=1`

#### Item Functions
**create_item**:
- **REQUIRED**: `intern_name` (internal item name)
- **AUTO-FILLED**: `user_id=1`, `article_type_id=1`, `currency_id=1`, `is_stock=false`, `delivery_price=0`

### Validation Flow
1. **Pre-validation**: Check for truly required user input fields
2. **Auto-completion**: Fill missing fields with safe defaults or lookups
3. **API call**: Submit completed data to Bexio API
4. **Error enhancement**: Provide helpful guidance if validation still fails
5. **Retry logic**: Automatic retry for recoverable validation errors

## Troubleshooting

### 422 Field Validation Errors
- **Enhanced handling**: The server now provides specific guidance for missing fields
- **Auto-completion**: Many required fields are filled automatically with safe defaults
- **Tax ID issues**: System automatically looks up valid tax IDs from your Bexio account
- **Contact updates**: Required fields like `nr` are retrieved from existing contact data

### 401 Authentication Failed
- **Most common issue**: Your Personal Access Token has expired (PAT tokens are valid for 6 months)
- **Solution**: Visit https://developer.bexio.com/pat and create a new token
- Update your `.env` file and Claude Desktop configuration with the new token
- Restart Claude Desktop after updating the configuration

### Connection Issues
- Check your internet connection
- Verify the Bexio API is accessible
- Ensure no firewall restrictions

### Rate Limiting
- Bexio API has rate limits - the server implements automatic retry logic
- Large result sets use pagination automatically
- Monitor API usage in your Bexio developer dashboard

## Project Structure

```
bexio-mcp-server/
├── mcp_server_bexio/
│   ├── __init__.py
│   ├── server.py
│   ├── bexio_client.py
│   └── field_validator.py
├── pyproject.toml
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: [https://github.com/tomasbottlik/bexio-mcp-server/issues](https://github.com/tomasbottlik/bexio-mcp-server/issues)
- Bexio API Documentation: [https://docs.bexio.com/](https://docs.bexio.com/)

## About

This MCP server enables seamless integration between AI assistants and Bexio business management software, allowing for natural language interaction with your business data.
