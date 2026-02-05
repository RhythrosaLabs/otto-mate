"""Settings API routes (v1)."""
from fastapi import APIRouter, Depends, HTTPException

from .dependencies import get_orchestrator
from .schemas import SettingsResponse, SettingsUpdateRequest, SuccessResponse

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_model=SettingsResponse)
async def get_settings(
    orchestrator = Depends(get_orchestrator)
):
    """Get current settings."""
    try:
        capabilities = orchestrator.get_capabilities()
        
        # Extract settings from capabilities
        api_keys = {}
        for integration in capabilities.get("integrations", []):
            key_name = integration.get("name")
            # Check if key is set (don't return actual values)
            api_keys[key_name] = integration.get("configured", False)
        
        models = {
            "default": capabilities.get("default_model", "claude-sonnet-4"),
            "available": capabilities.get("available_models", [])
        }
        
        features = capabilities.get("features", {})
        
        return SettingsResponse(
            api_keys=api_keys,
            models=models,
            features=features
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/", response_model=SuccessResponse)
async def update_settings(
    request: SettingsUpdateRequest,
    orchestrator = Depends(get_orchestrator)
):
    """Update settings."""
    try:
        # Update API keys
        if request.api_keys:
            for key_name, key_value in request.api_keys.items():
                # Update key in orchestrator config
                pass  # Implement actual key update logic
        
        # Update models
        if request.models:
            # Update model configuration
            pass  # Implement model update logic
        
        # Update features
        if request.features:
            # Update feature flags
            pass  # Implement feature update logic
        
        return SuccessResponse(
            success=True,
            message="Settings updated successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
