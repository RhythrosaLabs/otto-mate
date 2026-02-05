"""
Contacts Management Tools
========================

Tools for managing contacts, leads, and customer relationships.
Integrates with the chat system to automatically add contacts when researching.
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from .core import tool, ToolBase

logger = logging.getLogger(__name__)

# Data directory for contacts
DATA_DIR = Path("data/contacts")
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONTACTS_FILE = DATA_DIR / "contacts.json"


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
        description="Add a new contact to the CRM. Use this when you've researched someone and want to save their information.",
        category="contacts"
    )
    async def add_contact(
        self,
        name: str,
        email: Optional[str] = None,
        company: Optional[str] = None,
        phone: Optional[str] = None,
        contact_type: str = "lead",
        notes: Optional[str] = None,
        source: Optional[str] = None,
        social_links: Optional[Dict[str, str]] = None
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
            social_links: Dictionary of social media links (e.g., {"linkedin": "url", "twitter": "url"})
        
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
        description="Add multiple contacts at once. Use this when you've researched a list of people/influencers.",
        category="contacts"
    )
    async def add_multiple_contacts(
        self,
        contacts_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add multiple contacts at once.
        
        Args:
            contacts_list: List of contact dictionaries with name, email, company, etc.
        
        Returns:
            Summary of added contacts
        """
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
                    email=contact_data.get("email"),
                    company=contact_data.get("company"),
                    phone=contact_data.get("phone"),
                    contact_type=contact_data.get("type", "lead"),
                    notes=contact_data.get("notes"),
                    source=contact_data.get("source", "ai_research"),
                    social_links=contact_data.get("social_links")
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
