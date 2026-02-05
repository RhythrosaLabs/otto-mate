"""
Contacts Management Tools
========================

Tools for managing contacts, leads, and customer relationships.
Integrates with the chat system to automatically add contacts when researching.
"""

import logging
import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from .core import tool, ToolBase

logger = logging.getLogger(__name__)


def _get_contacts_file() -> Path:
    """Get the contacts file path, creating directory if needed."""
    # Try to find project root by looking for common markers
    cwd = Path.cwd()
    data_dir = cwd / "data" / "contacts"
    
    # Also try relative to this file's location
    if not (cwd / "data").exists():
        file_dir = Path(__file__).parent.parent.parent  # src/tools -> src -> project_root
        data_dir = file_dir / "data" / "contacts"
    
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"Could not create data directory: {e}")
        # Fallback to /tmp
        data_dir = Path("/tmp/otto/contacts")
        data_dir.mkdir(parents=True, exist_ok=True)
    
    return data_dir / "contacts.json"


CONTACTS_FILE = _get_contacts_file()


def load_contacts() -> List[Dict[str, Any]]:
    """Load contacts from file."""
    if CONTACTS_FILE.exists():
        try:
            with open(CONTACTS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading contacts: {e}")
    return []


def save_contacts(contacts: List[Dict[str, Any]]):
    """Save contacts to file."""
    try:
        with open(CONTACTS_FILE, 'w') as f:
            json.dump(contacts, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving contacts: {e}")


def generate_contact_id() -> str:
    """Generate unique contact ID."""
    return f"contact_{int(datetime.now().timestamp() * 1000)}"


class ContactsTools(ToolBase):
    """Contact management tools for the AI assistant."""
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        self.config = config or {}
    
    @tool(
        name="add_contact",
        description="Add a new contact to the CRM. Use this when you've researched someone and want to save their information. Only 'name' is required.",
        category="contacts",
        parameters={
            "name": {"type": "string", "description": "Full name of the contact", "required": True},
            "email": {"type": "string", "description": "Email address"},
            "company": {"type": "string", "description": "Company/organization name"},
            "phone": {"type": "string", "description": "Phone number"},
            "contact_type": {"type": "string", "description": "Type: lead, customer, contact, influencer, or partner"},
            "notes": {"type": "string", "description": "Additional notes about the contact"},
            "source": {"type": "string", "description": "Where this contact was found"},
            "linkedin": {"type": "string", "description": "LinkedIn URL"},
            "twitter": {"type": "string", "description": "Twitter/X URL"}
        }
    )
    async def add_contact(
        self,
        name: str,
        email: str = "",
        company: str = "",
        phone: str = "",
        contact_type: str = "lead",
        notes: str = "",
        source: str = "",
        linkedin: str = "",
        twitter: str = ""
    ) -> Dict[str, Any]:
        """
        Add a new contact to the system.
        
        Args:
            name: Full name of the contact
            email: Email address
            company: Company/organization name
            phone: Phone number
            contact_type: Type of contact (lead, customer, contact, influencer, partner)
            notes: Additional notes about the contact
            source: Where this contact was found (e.g., "web research", "referral")
            linkedin: LinkedIn profile URL
            twitter: Twitter/X profile URL
        
        Returns:
            The created contact object
        """
        contacts = load_contacts()
        
        # Check for duplicates by email
        if email:
            existing = next((c for c in contacts if c.get('email', '').lower() == email.lower()), None)
            if existing:
                return {
                    "success": False,
                    "error": f"Contact with email {email} already exists",
                    "existing_contact": existing
                }
        
        # Build social links from individual params
        social_links = {}
        if linkedin:
            social_links["linkedin"] = linkedin
        if twitter:
            social_links["twitter"] = twitter
        
        contact = {
            "id": generate_contact_id(),
            "name": name,
            "email": email or "",
            "company": company or "",
            "phone": phone or "",
            "type": contact_type,
            "notes": notes or "",
            "source": source or "ai_research",
            "social_links": social_links or {},
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        
        contacts.append(contact)
        save_contacts(contacts)
        
        logger.info(f"Added new contact: {name} ({email})")
        
        return {
            "success": True,
            "contact": contact,
            "message": f"Successfully added {name} to contacts"
        }
    
    @tool(
        name="add_multiple_contacts",
        description="Add multiple contacts at once. Pass a JSON array string of contacts. Each contact should have at least 'name', optionally 'email', 'company', 'type', 'notes', 'linkedin', 'twitter'.",
        category="contacts",
        parameters={
            "contacts_json": {"type": "string", "description": "JSON array string of contacts, e.g. '[{\"name\": \"John Doe\", \"email\": \"john@example.com\"}]'", "required": True}
        }
    )
    async def add_multiple_contacts(
        self,
        contacts_json: str
    ) -> Dict[str, Any]:
        """
        Add multiple contacts at once.
        
        Args:
            contacts_json: JSON string containing array of contact objects
        
        Returns:
            Summary of added contacts
        """
        # Parse the JSON string
        try:
            contacts_list = json.loads(contacts_json)
            if not isinstance(contacts_list, list):
                contacts_list = [contacts_list]  # Handle single object
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON: {str(e)}",
                "hint": "Pass a valid JSON array like '[{\"name\": \"John\", \"email\": \"john@example.com\"}]'"
            }
        
        results = {
            "success": True,
            "added": [],
            "skipped": [],
            "errors": []
        }
        
        for contact_data in contacts_list:
            try:
                name = contact_data.get("name")
                if not name:
                    results["errors"].append({"data": contact_data, "error": "Name is required"})
                    continue
                
                result = await self.add_contact(
                    name=name,
                    email=contact_data.get("email", ""),
                    company=contact_data.get("company", ""),
                    phone=contact_data.get("phone", ""),
                    contact_type=contact_data.get("type", "lead"),
                    notes=contact_data.get("notes", ""),
                    source=contact_data.get("source", "ai_research"),
                    linkedin=contact_data.get("linkedin", ""),
                    twitter=contact_data.get("twitter", "")
                )
                
                if result.get("success"):
                    results["added"].append(result["contact"])
                else:
                    results["skipped"].append({
                        "name": name,
                        "reason": result.get("error", "Already exists")
                    })
            except Exception as e:
                results["errors"].append({
                    "data": contact_data,
                    "error": str(e)
                })
        
        results["summary"] = f"Added {len(results['added'])} contacts, skipped {len(results['skipped'])}, {len(results['errors'])} errors"
        
        return results
    
    @tool(
        name="search_contacts",
        description="Search existing contacts by name, email, company, or type",
        category="contacts"
    )
    async def search_contacts(
        self,
        query: Optional[str] = None,
        contact_type: Optional[str] = None,
        company: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search contacts.
        
        Args:
            query: Search term (matches name, email, company, notes)
            contact_type: Filter by type (lead, customer, contact, influencer)
            company: Filter by company
        
        Returns:
            List of matching contacts
        """
        contacts = load_contacts()
        results = contacts
        
        if query:
            query_lower = query.lower()
            results = [
                c for c in results
                if query_lower in c.get('name', '').lower()
                or query_lower in c.get('email', '').lower()
                or query_lower in c.get('company', '').lower()
                or query_lower in c.get('notes', '').lower()
            ]
        
        if contact_type:
            results = [c for c in results if c.get('type') == contact_type]
        
        if company:
            company_lower = company.lower()
            results = [c for c in results if company_lower in c.get('company', '').lower()]
        
        return {
            "success": True,
            "count": len(results),
            "contacts": results
        }
    
    @tool(
        name="update_contact",
        description="Update an existing contact's information",
        category="contacts"
    )
    async def update_contact(
        self,
        contact_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a contact.
        
        Args:
            contact_id: ID of the contact to update
            updates: Dictionary of fields to update
        
        Returns:
            Updated contact object
        """
        contacts = load_contacts()
        contact = next((c for c in contacts if c['id'] == contact_id), None)
        
        if not contact:
            return {
                "success": False,
                "error": f"Contact {contact_id} not found"
            }
        
        # Update allowed fields
        allowed_fields = ['name', 'email', 'company', 'phone', 'type', 'notes', 'social_links', 'source']
        for field in allowed_fields:
            if field in updates:
                contact[field] = updates[field]
        
        contact['updatedAt'] = datetime.now().isoformat()
        save_contacts(contacts)
        
        return {
            "success": True,
            "contact": contact
        }
    
    @tool(
        name="delete_contact",
        description="Delete a contact by ID",
        category="contacts"
    )
    async def delete_contact(
        self,
        contact_id: str
    ) -> Dict[str, Any]:
        """
        Delete a contact.
        
        Args:
            contact_id: ID of the contact to delete
        
        Returns:
            Deletion result
        """
        contacts = load_contacts()
        original_count = len(contacts)
        contacts = [c for c in contacts if c['id'] != contact_id]
        
        if len(contacts) == original_count:
            return {
                "success": False,
                "error": f"Contact {contact_id} not found"
            }
        
        save_contacts(contacts)
        
        return {
            "success": True,
            "message": f"Contact {contact_id} deleted"
        }
    
    @tool(
        name="get_all_contacts",
        description="Get all contacts from the CRM",
        category="contacts"
    )
    async def get_all_contacts(self) -> Dict[str, Any]:
        """
        Get all contacts.
        
        Returns:
            All contacts in the system
        """
        contacts = load_contacts()
        
        return {
            "success": True,
            "count": len(contacts),
            "contacts": contacts,
            "by_type": {
                "leads": len([c for c in contacts if c.get('type') == 'lead']),
                "customers": len([c for c in contacts if c.get('type') == 'customer']),
                "contacts": len([c for c in contacts if c.get('type') == 'contact']),
                "influencers": len([c for c in contacts if c.get('type') == 'influencer'])
            }
        }
    
    @tool(
        name="research_and_add_influencers",
        description="Research influencers in a specific niche and add them to contacts. This searches the web for influencer information.",
        category="contacts"
    )
    async def research_and_add_influencers(
        self,
        niche: str,
        count: int = 10,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Research and add influencers in a niche.
        
        Args:
            niche: The niche/industry to find influencers in (e.g., "fitness", "tech", "fashion")
            count: Number of influencers to find
            platforms: Platforms to focus on (e.g., ["instagram", "youtube", "tiktok"])
        
        Returns:
            List of found and added influencers
        """
        platforms = platforms or ["instagram", "youtube", "twitter"]
        
        # Note: In a real implementation, this would use web search tools
        # For now, return a structured response for the AI to understand
        return {
            "success": True,
            "message": f"To research {niche} influencers, I should use web search tools to find influencers on {', '.join(platforms)}. After finding contact information, use add_multiple_contacts to save them.",
            "suggested_actions": [
                f"Search for 'top {niche} influencers {platforms[0]}'",
                f"Search for '{niche} content creators contact email'",
                "Extract names, emails, and social links from results",
                "Use add_multiple_contacts to save the found influencers"
            ]
        }


# Create a global instance for easy access
contacts_tools = ContactsTools()
