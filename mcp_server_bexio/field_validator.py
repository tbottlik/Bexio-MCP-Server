"""Field validation and completion system for Bexio MCP server."""

from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class FieldType(Enum):
    """Types of field handling for missing mandatory fields."""
    REQUIRED_USER_INPUT = "required_user_input"  # Must ask user
    AUTO_FILL_DEFAULT = "auto_fill_default"      # Can auto-fill with safe default
    AUTO_FILL_LOOKUP = "auto_fill_lookup"        # Can auto-fill by looking up existing data
    API_HANDLED = "api_handled"                  # API provides intelligent defaults


@dataclass
class FieldSpec:
    """Specification for a mandatory field."""
    name: str
    field_type: FieldType
    default_value: Any = None
    description: str = ""
    lookup_method: Optional[str] = None  # Method to call for lookup


class BexioFieldValidator:
    """Validates and completes mandatory fields for Bexio API calls."""
    
    # Define mandatory fields for each function
    FIELD_SPECS = {
        # Contact functions
        "create_contact": [
            FieldSpec("name_1", FieldType.REQUIRED_USER_INPUT, description="Contact name (company name or first name)"),
            FieldSpec("contact_type_id", FieldType.AUTO_FILL_DEFAULT, 2, "Contact type (1=company, 2=person)"),
            FieldSpec("user_id", FieldType.AUTO_FILL_DEFAULT, 1, "User ID (typically 1)"),
            FieldSpec("owner_id", FieldType.AUTO_FILL_DEFAULT, 1, "Owner ID (typically 1)"),
        ],
        "update_contact": [
            FieldSpec("name_1", FieldType.AUTO_FILL_LOOKUP, lookup_method="get_contact", description="Contact name"),
            FieldSpec("contact_type_id", FieldType.AUTO_FILL_LOOKUP, lookup_method="get_contact", description="Contact type"),
            FieldSpec("nr", FieldType.API_HANDLED, description="Contact number (API handles gracefully)"),
            FieldSpec("user_id", FieldType.AUTO_FILL_LOOKUP, lookup_method="get_contact", description="User ID"),
            FieldSpec("owner_id", FieldType.AUTO_FILL_LOOKUP, lookup_method="get_contact", description="Owner ID"),
        ],
        
        # Invoice functions
        "create_invoice": [
            FieldSpec("contact_id", FieldType.REQUIRED_USER_INPUT, description="Contact ID for the invoice"),
            FieldSpec("user_id", FieldType.AUTO_FILL_DEFAULT, 1, "User ID (typically 1)"),
            FieldSpec("positions", FieldType.REQUIRED_USER_INPUT, description="Invoice line items array"),
        ],
        
        # Quote functions  
        "create_quote": [
            FieldSpec("contact_id", FieldType.REQUIRED_USER_INPUT, description="Contact ID for the quote"),
            FieldSpec("user_id", FieldType.AUTO_FILL_DEFAULT, 1, "User ID (typically 1)"),
        ],
        
        # Project functions
        "create_project": [
            FieldSpec("name", FieldType.REQUIRED_USER_INPUT, description="Project name"),
            FieldSpec("contact_id", FieldType.REQUIRED_USER_INPUT, description="Contact ID for the project"),
            FieldSpec("user_id", FieldType.AUTO_FILL_DEFAULT, 1, "User ID (typically 1)"),
            FieldSpec("pr_state_id", FieldType.AUTO_FILL_DEFAULT, 1, "Project state ID (1=active)"),
            FieldSpec("pr_project_type_id", FieldType.AUTO_FILL_DEFAULT, 1, "Project type ID (1=default)"),
        ],
        
        # Item functions
        "create_item": [
            FieldSpec("intern_name", FieldType.REQUIRED_USER_INPUT, description="Internal item name"),
        ],
        
        # Search functions - all require criteria
        "search_contacts": [
            FieldSpec("criteria", FieldType.REQUIRED_USER_INPUT, description="Search criteria array with field, value, criteria"),
        ],
        "search_invoices": [
            FieldSpec("criteria", FieldType.REQUIRED_USER_INPUT, description="Search criteria array"),
        ],
        "search_quotes": [
            FieldSpec("criteria", FieldType.REQUIRED_USER_INPUT, description="Search criteria array"),
        ],
    }
    
    # Default values for invoice positions when user doesn't provide complete data
    DEFAULT_INVOICE_POSITION = {
        "type": "KbPositionCustom",
        "amount": 1,
        "unit_price": 0.0,
        "tax_id": None  # Will be looked up from valid taxes
    }

    def __init__(self, bexio_client=None):
        """Initialize validator with optional Bexio client for lookups."""
        self.bexio_client = bexio_client

    async def validate_and_complete_fields(
        self, 
        function_name: str, 
        data: Dict[str, Any],
        context_id: Optional[int] = None
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Validate and complete mandatory fields for a function call.
        
        Args:
            function_name: Name of the Bexio function being called
            data: Input data dictionary
            context_id: ID for lookup operations (e.g., contact_id for updates)
            
        Returns:
            Tuple of (completed_data, missing_fields_requiring_user_input)
        """
        if function_name not in self.FIELD_SPECS:
            return data, []
            
        field_specs = self.FIELD_SPECS[function_name]
        completed_data = dict(data)
        missing_user_fields = []
        
        # Handle nested data structures (e.g., contact_data, invoice_data)
        data_key = self._get_data_key(function_name)
        if data_key and data_key in completed_data:
            nested_data = completed_data[data_key]
        else:
            nested_data = completed_data
            
        for field_spec in field_specs:
            field_name = field_spec.name
            
            # Skip if field already provided
            if field_name in nested_data and nested_data[field_name] is not None:
                # Special handling for positions array in invoices
                if field_name == "positions" and function_name == "create_invoice":
                    nested_data[field_name] = await self._complete_invoice_positions(nested_data[field_name])
                continue
                
            # Handle missing field based on type
            if field_spec.field_type == FieldType.REQUIRED_USER_INPUT:
                missing_user_fields.append(f"{field_name}: {field_spec.description}")
                
            elif field_spec.field_type == FieldType.AUTO_FILL_DEFAULT:
                nested_data[field_name] = field_spec.default_value
                
            elif field_spec.field_type == FieldType.AUTO_FILL_LOOKUP and self.bexio_client:
                try:
                    lookup_value = await self._lookup_field_value(
                        field_spec.lookup_method, 
                        context_id, 
                        field_name
                    )
                    if lookup_value is not None:
                        nested_data[field_name] = lookup_value
                    else:
                        missing_user_fields.append(f"{field_name}: {field_spec.description} (lookup failed)")
                except Exception:
                    missing_user_fields.append(f"{field_name}: {field_spec.description} (lookup error)")
                    
            elif field_spec.field_type == FieldType.API_HANDLED:
                # Skip - API will handle this field with intelligent defaults
                continue
        
        # Update the completed data
        if data_key and data_key in completed_data:
            completed_data[data_key] = nested_data
        else:
            completed_data = nested_data
            
        return completed_data, missing_user_fields

    def _get_data_key(self, function_name: str) -> Optional[str]:
        """Get the nested data key for functions that use nested data structures."""
        data_key_map = {
            "create_contact": "contact_data",
            "update_contact": "contact_data", 
            "create_invoice": "invoice_data",
            "create_quote": "quote_data",
            "create_project": "project_data",
            "create_item": "item_data",
        }
        return data_key_map.get(function_name)

    async def _complete_invoice_positions(self, positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Complete invoice positions with required fields."""
        completed_positions = []
        
        # Get valid tax_id if not already cached
        default_tax_id = await self._get_default_tax_id()
        
        for pos in positions:
            completed_pos = {**self.DEFAULT_INVOICE_POSITION, **pos}
            
            # Ensure required fields are present
            if "text" not in completed_pos:
                completed_pos["text"] = "Service"
            if "amount" not in completed_pos:
                completed_pos["amount"] = 1
            if "unit_price" not in completed_pos:
                completed_pos["unit_price"] = 0.0
            if "tax_id" not in completed_pos or completed_pos["tax_id"] is None:
                completed_pos["tax_id"] = default_tax_id
                
            completed_positions.append(completed_pos)
            
        return completed_positions

    async def _lookup_field_value(
        self, 
        lookup_method: str, 
        context_id: int, 
        field_name: str
    ) -> Any:
        """Look up a field value from existing data."""
        if not self.bexio_client or not context_id:
            return None
            
        try:
            if lookup_method == "get_contact":
                existing_data = await self.bexio_client.get_contact(context_id)
                return existing_data.get(field_name)
            # Add other lookup methods as needed
            
        except Exception:
            return None
            
        return None

    async def _get_default_tax_id(self) -> int:
        """Get a valid default tax_id from the Bexio system."""
        if not self.bexio_client:
            return 1  # Fallback
            
        try:
            # Try to get available taxes from the system
            taxes = await self.bexio_client.get("/tax")
            if taxes and len(taxes) > 0:
                # Find a standard tax rate (usually VAT/MwSt)
                for tax in taxes:
                    if tax.get("is_active", True) and tax.get("percentage", 0) > 0:
                        return tax.get("id", 1)
                # Fallback to first available tax
                return taxes[0].get("id", 1)
        except Exception:
            # If tax lookup fails, try common tax IDs
            pass
            
        # Common fallback tax IDs in Swiss Bexio systems
        return 1

    def create_user_prompt_message(self, missing_fields: List[str]) -> str:
        """Create a user-friendly message for missing required fields."""
        if not missing_fields:
            return ""
            
        message = "Missing required fields:\n"
        for field in missing_fields:
            message += f"• {field}\n"
            
        message += "\nPlease provide the missing information and try again."
        return message

    def parse_422_error(self, error_message: str) -> List[str]:
        """Parse a 422 error message to extract missing field information."""
        missing_fields = []
        
        # Enhanced 422 error patterns from Bexio API
        if "errors" in error_message.lower():
            # Check for invalid value errors (not just missing fields)
            if "diese eingabe ist nicht korrekt" in error_message.lower():
                if "tax_id" in error_message:
                    missing_fields.append("tax_id: Invalid tax ID value. The system will now lookup valid tax IDs automatically.")
                return missing_fields
            
            # Try to extract field names from error message
            if "name_1" in error_message:
                missing_fields.append("name_1: Contact name is required")
            if "contact_type_id" in error_message:
                missing_fields.append("contact_type_id: Contact type is required (1=company, 2=person)")
            if "user_id" in error_message:
                missing_fields.append("user_id: User ID is required")
            if "contact_id" in error_message:
                missing_fields.append("contact_id: Contact ID is required")
            if "nr" in error_message and "pflichtfeld" in error_message.lower():
                missing_fields.append("nr: Contact number is required (will be retrieved from existing contact)")
                
        return missing_fields
