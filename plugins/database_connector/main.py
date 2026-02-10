"""
Database Connector Plugin
========================

Connect to and query databases.

Supports:
- SQLite (built-in)
- PostgreSQL (requires psycopg2)
- MySQL (requires mysql-connector-python)
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.core.plugin_system import IntegrationPlugin


class DatabaseConnectorPlugin(IntegrationPlugin):
    """Plugin for database connections and queries."""
    
    def __init__(self, settings: Dict[str, Any] = None):
        super().__init__(settings)
        self._connection = None
        self._db_type = None
    
    async def initialize(self) -> None:
        """Initialize the plugin and register tools."""
        
        # Query tool
        self.register_tool(
            name="query_database",
            func=self.query_database,
            description="Execute a SQL query and return results",
            parameters={
                "query": {
                    "type": "string",
                    "required": True,
                    "description": "SQL query to execute"
                },
                "params": {
                    "type": "array",
                    "required": False,
                    "description": "Query parameters for prepared statements"
                }
            }
        )
        
        # List tables
        self.register_tool(
            name="list_tables",
            func=self.list_tables,
            description="List all tables in the database",
            parameters={}
        )
        
        # Describe table
        self.register_tool(
            name="describe_table",
            func=self.describe_table,
            description="Get schema information for a table",
            parameters={
                "table_name": {
                    "type": "string",
                    "required": True,
                    "description": "Name of the table to describe"
                }
            }
        )
        
        # Insert data
        self.register_tool(
            name="insert_data",
            func=self.insert_data,
            description="Insert data into a table",
            parameters={
                "table_name": {
                    "type": "string",
                    "required": True,
                    "description": "Name of the table"
                },
                "data": {
                    "type": "object",
                    "required": True,
                    "description": "Data to insert as key-value pairs"
                }
            }
        )
    
    async def connect(self) -> bool:
        """Connect to the database."""
        db_type = self.settings.get("db_type", "sqlite")
        self._db_type = db_type
        
        try:
            if db_type == "sqlite":
                db_path = self.settings.get("db_path", "")
                if not db_path:
                    # Use in-memory database for testing
                    db_path = ":memory:"
                
                self._connection = sqlite3.connect(db_path)
                self._connection.row_factory = sqlite3.Row
                
            elif db_type == "postgresql":
                try:
                    import psycopg2
                    import psycopg2.extras
                except ImportError:
                    raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")
                
                self._connection = psycopg2.connect(
                    host=self.settings.get("db_host", "localhost"),
                    port=self.settings.get("db_port", 5432),
                    database=self.settings.get("db_name", ""),
                    user=self.settings.get("db_user", ""),
                    password=self.settings.get("db_password", "")
                )
                
            elif db_type == "mysql":
                try:
                    import mysql.connector
                except ImportError:
                    raise ImportError("mysql-connector-python not installed. Run: pip install mysql-connector-python")
                
                self._connection = mysql.connector.connect(
                    host=self.settings.get("db_host", "localhost"),
                    port=self.settings.get("db_port", 3306),
                    database=self.settings.get("db_name", ""),
                    user=self.settings.get("db_user", ""),
                    password=self.settings.get("db_password", "")
                )
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            self._connected = True
            return True
            
        except Exception as e:
            self._connected = False
            raise e
    
    async def disconnect(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
        self._connected = False
    
    def _ensure_connected(self):
        """Ensure we have a database connection."""
        if not self._connection:
            import asyncio
            asyncio.get_event_loop().run_until_complete(self.connect())
    
    async def query_database(
        self, 
        query: str, 
        params: List[Any] = None
    ) -> Dict[str, Any]:
        """Execute a SQL query."""
        self._ensure_connected()
        
        max_rows = self.settings.get("max_rows", 100)
        
        try:
            cursor = self._connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Check if it's a SELECT query
            if query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchmany(max_rows)
                
                # Get column names
                if self._db_type == "sqlite":
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    results = [dict(zip(columns, row)) for row in rows]
                else:
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    results = [dict(zip(columns, row)) for row in rows]
                
                return {
                    "success": True,
                    "row_count": len(results),
                    "columns": columns,
                    "data": results
                }
            else:
                # For INSERT, UPDATE, DELETE
                self._connection.commit()
                return {
                    "success": True,
                    "rows_affected": cursor.rowcount,
                    "message": f"Query executed successfully. {cursor.rowcount} rows affected."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_tables(self) -> Dict[str, Any]:
        """List all tables in the database."""
        self._ensure_connected()
        
        try:
            if self._db_type == "sqlite":
                query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            elif self._db_type == "postgresql":
                query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """
            elif self._db_type == "mysql":
                query = "SHOW TABLES"
            else:
                return {"success": False, "error": f"Unsupported database: {self._db_type}"}
            
            result = await self.query_database(query)
            
            if result["success"]:
                tables = [list(row.values())[0] for row in result.get("data", [])]
                return {
                    "success": True,
                    "table_count": len(tables),
                    "tables": tables
                }
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def describe_table(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a table."""
        self._ensure_connected()
        
        # Sanitize table name (basic protection)
        if not table_name.isidentifier():
            return {"success": False, "error": "Invalid table name"}
        
        try:
            if self._db_type == "sqlite":
                query = f"PRAGMA table_info({table_name})"
                result = await self.query_database(query)
                
                if result["success"]:
                    columns = []
                    for row in result.get("data", []):
                        columns.append({
                            "name": row.get("name"),
                            "type": row.get("type"),
                            "nullable": not row.get("notnull"),
                            "primary_key": bool(row.get("pk")),
                            "default": row.get("dflt_value")
                        })
                    return {
                        "success": True,
                        "table": table_name,
                        "column_count": len(columns),
                        "columns": columns
                    }
                    
            elif self._db_type == "postgresql":
                query = f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """
                result = await self.query_database(query, [table_name])
                
                if result["success"]:
                    columns = []
                    for row in result.get("data", []):
                        columns.append({
                            "name": row.get("column_name"),
                            "type": row.get("data_type"),
                            "nullable": row.get("is_nullable") == "YES",
                            "default": row.get("column_default")
                        })
                    return {
                        "success": True,
                        "table": table_name,
                        "column_count": len(columns),
                        "columns": columns
                    }
                    
            elif self._db_type == "mysql":
                query = f"DESCRIBE {table_name}"
                result = await self.query_database(query)
                
                if result["success"]:
                    columns = []
                    for row in result.get("data", []):
                        columns.append({
                            "name": row.get("Field"),
                            "type": row.get("Type"),
                            "nullable": row.get("Null") == "YES",
                            "primary_key": row.get("Key") == "PRI",
                            "default": row.get("Default")
                        })
                    return {
                        "success": True,
                        "table": table_name,
                        "column_count": len(columns),
                        "columns": columns
                    }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def insert_data(
        self, 
        table_name: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Insert a row into a table."""
        self._ensure_connected()
        
        # Sanitize table name
        if not table_name.isidentifier():
            return {"success": False, "error": "Invalid table name"}
        
        if not data:
            return {"success": False, "error": "No data provided"}
        
        try:
            columns = list(data.keys())
            values = list(data.values())
            
            # Build parameterized query
            col_str = ", ".join(columns)
            
            if self._db_type == "sqlite":
                placeholders = ", ".join(["?" for _ in values])
            else:
                placeholders = ", ".join(["%s" for _ in values])
            
            query = f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders})"
            
            result = await self.query_database(query, values)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Inserted 1 row into {table_name}",
                    "data": data
                }
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
