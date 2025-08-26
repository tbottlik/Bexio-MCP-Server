"""General field validation and completion system for Bexio MCP server."""

from typing import Any, Dict, List, Optional, Tuple


class BexioFieldValidator:
    """General field validator that works with any field specification."""
    
    def __init__(self, bexio_client=None):
        """Initialize validator with optional Bexio client for lookups."""
        self.bexio_client = bexio_client

    async def auto_complete_fields(self, function_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-complete fields with safe defaults where possible."""
        completed_data = dict(data)
        
        # Handle nested data structures
        data_key = self._get_data_key(function_name)
        if data_key and data_key in completed_data:
            nested_data = completed_data[data_key]
        else:
            nested_data = completed_data
            
        # Auto-complete fields for creation/update operations
        if function_name in ["create_contact", "update_contact", "create_invoice", "update_invoice", "create_quote", "update_quote", "create_project", "update_project", "create_item"]:
            # Auto-fill common defaults
            if "user_id" not in nested_data:
                nested_data["user_id"] = 1
                
        if function_name == "create_contact":
            if "contact_type_id" not in nested_data:
                nested_data["contact_type_id"] = 2  # Person
            if "owner_id" not in nested_data:
                nested_data["owner_id"] = 1
                
        if function_name == "create_project":
            if "pr_state_id" not in nested_data:
                nested_data["pr_state_id"] = 1
            if "pr_project_type_id" not in nested_data:
                nested_data["pr_project_type_id"] = 1
                
        if function_name == "create_item":
            if "article_type_id" not in nested_data:
                nested_data["article_type_id"] = 1
            if "currency_id" not in nested_data:
                nested_data["currency_id"] = 1
            if "is_stock" not in nested_data:
                nested_data["is_stock"] = False
            if "delivery_price" not in nested_data:
                nested_data["delivery_price"] = 0
                
        # Handle invoice positions
        if function_name == "create_invoice" and "positions" in nested_data:
            nested_data["positions"] = await self._complete_invoice_positions(nested_data["positions"])
            
        # Handle updates - lookup existing data for entities that have nr fields
        if function_name == "update_contact":
            contact_id = data.get("contact_id")
            if contact_id and self.bexio_client:
                try:
                    existing = await self.bexio_client.get_contact(contact_id)
                    # Fill in missing required fields from existing contact
                    for field in ["name_1", "contact_type_id", "user_id", "owner_id", "nr"]:
                        if field not in nested_data and field in existing:
                            nested_data[field] = existing[field]
                except Exception:
                    pass
                    
        # Handle invoice updates if they exist (invoices also have nr fields)
        if function_name == "update_invoice":
            invoice_id = data.get("invoice_id")
            if invoice_id and self.bexio_client:
                try:
                    existing = await self.bexio_client.get_invoice(invoice_id)
                    # Fill in missing required fields from existing invoice
                    for field in ["contact_id", "user_id", "nr"]:
                        if field not in nested_data and field in existing:
                            nested_data[field] = existing[field]
                except Exception:
                    pass
                    
        # Handle quote updates if they exist (quotes also have nr fields)  
        if function_name == "update_quote":
            quote_id = data.get("quote_id")
            if quote_id and self.bexio_client:
                try:
                    existing = await self.bexio_client.get_quote(quote_id)
                    # Fill in missing required fields from existing quote
                    for field in ["contact_id", "user_id", "nr"]:
                        if field not in nested_data and field in existing:
                            nested_data[field] = existing[field]
                except Exception:
                    pass
                    
        # Handle project updates if they exist (projects also have nr fields)
        if function_name == "update_project":
            project_id = data.get("project_id")
            if project_id and self.bexio_client:
                try:
                    existing = await self.bexio_client.get_project(project_id)
                    # Fill in missing required fields from existing project
                    for field in ["name", "contact_id", "user_id", "pr_state_id", "pr_project_type_id", "nr"]:
                        if field not in nested_data and field in existing:
                            nested_data[field] = existing[field]
                except Exception:
                    pass
        
        # Update the completed data
        if data_key and data_key in completed_data:
            completed_data[data_key] = nested_data
        else:
            completed_data = nested_data
            
        return completed_data

    def _get_data_key(self, function_name: str) -> str:
        """Get the data key for nested data structures."""
        data_keys = {
            "create_contact": "contact_data",
            "update_contact": "contact_data",
            "update_invoice": "invoice_data",
            "update_quote": "quote_data",
            "create_project": "project_data",
            "update_project": "project_data",
            "create_item": "item_data",
            "update_item": "item_data"
        }
        return data_keys.get(function_name)

    async def _complete_invoice_positions(self, positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Complete invoice positions with required fields."""
        completed_positions = []
        default_tax_id = await self._get_default_tax_id()
        
        for pos in positions:
            completed_pos = dict(pos)
            
            # Ensure required fields are present
            if "type" not in completed_pos:
                completed_pos["type"] = "KbPositionCustom"
            if "text" not in completed_pos:
                completed_pos["text"] = "Service"
            if "amount" not in completed_pos:
                completed_pos["amount"] = 1
            if "unit_price" not in completed_pos:
                completed_pos["unit_price"] = 0.0
            if "tax_id" not in completed_pos:
                completed_pos["tax_id"] = default_tax_id
                
            completed_positions.append(completed_pos)
            
        return completed_positions

    async def _get_default_tax_id(self) -> int:
        """Get a valid default tax_id from the Bexio system."""
        if not self.bexio_client:
            return 1
            
        try:
            # Use the correct Bexio API endpoint for taxes
            taxes = await self.bexio_client._request("GET", "/2.0/taxes")
            if taxes and len(taxes) > 0:
                # Find the first active tax (Swiss VAT is typically id=1)
                for tax in taxes:
                    if tax.get("is_active", True):
                        return tax.get("id", 1)
                # Fallback to first tax if none marked active
                return taxes[0].get("id", 1)
        except Exception as e:
            # If tax lookup fails, try Tax ID 3 first (confirmed working), then others
            for fallback_id in [3, 1, 2]:
                try:
                    # Test if this tax_id exists by trying to fetch it
                    await self.bexio_client._request("GET", f"/2.0/taxes/{fallback_id}")
                    return fallback_id
                except Exception:
                    continue
            
        # Final fallback - Use Tax ID 3 (0% rate) as confirmed working in this Bexio system
        return 3

    def create_helpful_error_message(self, error_message: str) -> str:
        """Create a helpful error message for any 422 error."""
        if "422" not in error_message and "HTTP 422" not in error_message:
            return error_message
            
        base_msg = "Bexio API Error (422 - Validation Failed): "
        
        # General guidance without being too specific to current error formats
        if any(keyword in error_message.lower() for keyword in ["pflichtfeld", "required", "missing"]):
            base_msg += "Some required fields are missing. "
        elif any(keyword in error_message.lower() for keyword in ["nicht korrekt", "invalid", "incorrect"]):
            base_msg += "Some field values are invalid. "
        else:
            base_msg += "Field validation failed. "
            
        base_msg += "The system will attempt to auto-complete missing fields and retry. "
        base_msg += f"Original error: {error_message}"
        
        return base_msg
