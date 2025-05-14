from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import logging
import traceback
from pydantic import ValidationError
import json
import aiohttp

from ..services.auth import get_current_user, User
from ..models.integrations import (
    Integration, 
    IntegrationCreate, 
    IntegrationUpdate,
    SlackIntegration,
    WebsiteIntegration,
    SlackEventPayload
)
from ..db.firebase import FirestoreDB
from ..services.integrations import slack_handler, website_handler

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()
firestore_db = FirestoreDB()

@router.get("/", response_model=List[Integration])
async def list_integrations(current_user: User = Depends(get_current_user)):
    """List all integrations for the current user"""
    try:
        # Get integrations from database
        integrations = await firestore_db.list_integrations(current_user.id)
        return integrations
    except Exception as e:
        logger.error(f"Error listing integrations: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list integrations: {str(e)}"
        )

@router.post("/{type}", response_model=Integration)
async def create_integration(
    type: str,
    integration_data: IntegrationCreate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Create a new integration (Slack or Website only)"""
    try:
        # Validate integration type - Only allow 'slack' and 'website'
        if type not in ["slack", "website"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or unsupported integration type: {type}. Only 'slack' and 'website' are supported."
            )
        
        # Verify type matches the one in the path
        if integration_data.type != type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Integration type mismatch: {integration_data.type} != {type}"
            )
        
        # Generate unique ID for integration
        integration_id = str(uuid.uuid4())
        
        # Create integration in database
        integration_dict = {
            "id": integration_id,
            "type": type,
            "name": integration_data.name,
            "status": "pending",  # New integrations start as pending
            "userId": current_user.id,
            "chatbotId": integration_data.chatbotId,
            "config": integration_data.config,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now()
        }
        
        # Use the appropriate handler to process the integration
        # In a real implementation, this would call a specific handler for each type
        # For this example, we'll just create the integration
        await firestore_db.create_integration(integration_dict)
        
        # Process the integration based on type (simplified version)
        # In a real implementation, this would have more complexity
        result = await process_integration(type, integration_dict)
        
        # Return the created integration
        return result
    except ValidationError as e:
        logger.error(f"Validation error creating integration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid integration data: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating integration: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create integration: {str(e)}"
        )

@router.get("/{integration_id}", response_model=Integration)
async def get_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get integration details"""
    try:
        # Get integration from database
        integration = await firestore_db.get_integration(integration_id)
        
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        # Check if user owns the integration
        if integration.get("userId") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this integration"
            )
        
        return integration
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting integration: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration: {str(e)}"
        )

@router.put("/{integration_id}", response_model=Integration)
async def update_integration(
    integration_id: str,
    integration_data: IntegrationUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Update an integration"""
    try:
        # Get integration from database
        integration = await firestore_db.get_integration(integration_id)
        
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        # Check if user owns the integration
        if integration.get("userId") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this integration"
            )
        
        # Prepare update data
        update_data = {}
        if integration_data.name is not None:
            update_data["name"] = integration_data.name
        if integration_data.status is not None:
            update_data["status"] = integration_data.status
        if integration_data.chatbotId is not None:
            update_data["chatbotId"] = integration_data.chatbotId
        if integration_data.config is not None:
            update_data["config"] = integration_data.config
        
        update_data["updatedAt"] = datetime.now()
        
        # Update integration in database
        await firestore_db.update_integration(integration_id, update_data)
        
        # Get updated integration
        updated_integration = await firestore_db.get_integration(integration_id)
        
        # Process the integration if status has changed to "active"
        if (
            integration_data.status == "active" and
            integration.get("status") != "active"
        ):
            updated_integration = await process_integration(
                updated_integration.get("type"),
                updated_integration
            )
        
        return updated_integration
    except ValidationError as e:
        logger.error(f"Validation error updating integration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid integration data: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating integration: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update integration: {str(e)}"
        )

@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an integration"""
    try:
        # Get integration from database
        integration = await firestore_db.get_integration(integration_id)
        
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        # Check if user owns the integration
        if integration.get("userId") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this integration"
            )
        
        # Delete integration in database
        await firestore_db.delete_integration(integration_id)
        
        # Clean up integration resources
        # In a real implementation, this would depend on the integration type
        # For example, removing webhooks, deleting DNS records, etc.
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting integration: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete integration: {str(e)}"
        )

@router.post("/slack/events")
async def handle_slack_events(request: Request):
    """Handle incoming Slack events"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        body_str = body.decode()
        
        # Log the incoming event for debugging
        logger.info(f"Received Slack event: {body_str}")
        
        # Parse event data
        event_data = json.loads(body_str)
        
        # Handle URL verification challenge
        if event_data.get("type") == "url_verification":
            logger.info("Handling Slack URL verification challenge")
            return {"challenge": event_data.get("challenge")}
        
        # For other events, verify Slack signature
        timestamp = request.headers.get("X-Slack-Request-Timestamp")
        signature = request.headers.get("X-Slack-Signature")
        
        if not timestamp or not signature:
            logger.error("Missing Slack verification headers")
            logger.error(f"Headers: {dict(request.headers)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Slack verification headers"
            )
            
        # Get team_id from the event data
        team_id = event_data.get("team_id")
        if not team_id:
            logger.error("Missing team_id in event data")
            logger.error(f"Event data: {event_data}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing team_id in event data"
            )
            
        # Log that we're searching for the integration
        logger.info(f"Searching for integration with team_id: {team_id}")
        
        # Find the Slack integration for this team
        integrations = await firestore_db.list_integrations_by_query(
            field_path="config.team_id",
            op_string="==",
            value=team_id
        )
        
        if not integrations:
            logger.error(f"No integration found for team_id: {team_id}")
            # List all integrations for debugging
            all_integrations = await firestore_db.list_integrations(None)  # Pass None to get all integrations
            logger.error(f"Available integrations: {json.dumps(all_integrations, indent=2)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
            
        integration = integrations[0]  # Use the first matching integration
        logger.info(f"Found integration: {integration.get('id')}")
        
        # Get credentials from the integration
        config = integration.get("config", {})
        bot_token = config.get("bot_token")
        signing_secret = config.get("signing_secret")
        
        if not bot_token or not signing_secret:
            logger.error("Missing Slack credentials in integration config")
            logger.error(f"Integration config: {json.dumps(config, indent=2)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Integration not properly configured"
            )
            
        # Get chatbot settings if available
        chatbot_id = integration.get("chatbotId")
        chatbot_settings = None
        if chatbot_id:
            chatbot = await firestore_db.get_chatbot(chatbot_id)
            if chatbot and "settings" in chatbot:
                chatbot_settings = chatbot["settings"]
                logger.info(f"Using chatbot settings from chatbot: {chatbot_id}")
            else:
                logger.warning(f"No settings found for chatbot: {chatbot_id}")
        else:
            logger.warning("No chatbot ID associated with this integration")
        
        # Set up Slack handler with credentials and settings
        slack_handler.set_credentials(bot_token, signing_secret, chatbot_settings)
        
        # Verify request is from Slack
        is_valid = await slack_handler.verify_request_signature(
            timestamp=timestamp,
            signature=signature,
            body=body_str
        )
        
        if not is_valid:
            logger.error("Invalid Slack signature")
            logger.error(f"Timestamp: {timestamp}")
            logger.error(f"Signature: {signature}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Slack signature"
            )
        
        # Handle the event
        logger.info("Processing Slack event")
        result = await slack_handler.handle_event(event_data)
        
        if result:
            logger.info(f"Event handled successfully: {result}")
            return result
            
        logger.info("Event processed successfully")
        return {"status": "ok"}
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling Slack event: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Slack event: {str(e)}"
        )

@router.post("/slack/{integration_id}/credentials")
async def update_slack_credentials(
    integration_id: str,
    credentials: Dict[str, str] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Update Slack integration credentials"""
    try:
        # Get integration from database
        integration = await firestore_db.get_integration(integration_id)
        
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        # Check if user owns the integration
        if integration.get("userId") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this integration"
            )
        
        # Validate integration type
        if integration.get("type") != "slack":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not a Slack integration"
            )
        
        # Get bot token and signing secret
        bot_token = credentials.get("botToken") or credentials.get("bot_token")
        signing_secret = credentials.get("signingSecret") or credentials.get("signing_secret")
        
        if not bot_token or not signing_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot token and signing secret are required"
            )
        
        # Verify bot token and get team info
        try:
            session = aiohttp.ClientSession()
            headers = {
                "Authorization": f"Bearer {bot_token}",
                "Content-Type": "application/json"
            }
            
            async with session.post("https://slack.com/api/auth.test", headers=headers) as response:
                data = await response.json()
                if not data.get("ok"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid bot token: {data.get('error')}"
                    )
                
                # Update config with credentials and team info
                config = integration.get("config", {})
                config.update({
                    "bot_token": bot_token,
                    "signing_secret": signing_secret,
                    "team_id": data.get("team_id"),
                    "team_name": data.get("team")
                })
                
                # Update integration with verified credentials
                await firestore_db.update_integration(
                    integration_id,
                    {
                        "config": config,
                        "updatedAt": datetime.now(),
                        "status": "pending"  # Reset status to let process_integration verify everything
                    }
                )
        except Exception as e:
            logger.error(f"Error verifying Slack credentials: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to verify Slack credentials: {str(e)}"
            )
        finally:
            if session and not session.closed:
                await session.close()
        
        # Reprocess integration
        updated_integration = await firestore_db.get_integration(integration_id)
        result = await process_integration("slack", updated_integration)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Slack credentials: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update credentials: {str(e)}"
        )

# Helper function to process integrations based on type
async def process_integration(integration_type: str, integration_data: Dict[str, Any]) -> Integration:
    """Process an integration based on its type"""
    try:
        # Get chatbot settings if available
        chatbot_id = integration_data.get("chatbotId")
        chatbot_settings = None
        
        if chatbot_id:
            # Get chatbot from database
            chatbot = await firestore_db.get_chatbot(chatbot_id)
            if chatbot and "settings" in chatbot:
                chatbot_settings = chatbot["settings"]
        
        if integration_type == "slack":
            config = integration_data.get("config", {})
            bot_token = config.get("bot_token")
            signing_secret = config.get("signing_secret")
            
            if not bot_token or not signing_secret:
                logger.warning("Slack integration missing required credentials")
                integration_data["status"] = "error"
                integration_data["error"] = "Missing required credentials"
                return integration_data
            
            # Set up Slack handler with credentials and chatbot settings
            slack_handler.set_credentials(bot_token, signing_secret, chatbot_settings)
            
            # First, verify the bot token by making a simple auth.test API call
            try:
                session = await slack_handler._get_session()
                headers = {
                    "Authorization": f"Bearer {bot_token}",
                    "Content-Type": "application/json"
                }
                
                # Call auth.test to verify token and get team info
                async with session.post("https://slack.com/api/auth.test", headers=headers) as response:
                    data = await response.json()
                    if data.get("ok"):
                        # Save the team_id and team_name from auth.test response
                        config["team_id"] = data.get("team_id")
                        config["team_name"] = data.get("team")
                        integration_data["config"] = config
                    else:
                        logger.error(f"Error verifying bot token: {data.get('error')}")
                        integration_data["status"] = "error"
                        integration_data["error"] = f"Invalid bot token: {data.get('error')}"
                        return integration_data
                
                # Try to get additional team info if we have the right scope
                try:
                    async with session.get("https://slack.com/api/team.info", headers=headers) as response:
                        data = await response.json()
                        if data.get("ok"):
                            team = data.get("team", {})
                            # Update with additional team info if available
                            if not config.get("team_name"):
                                config["team_name"] = team.get("name")
                            integration_data["config"] = config
                except Exception as e:
                    # Log the error but don't fail the integration
                    logger.warning(f"Could not get additional team info: {str(e)}")
                
                # Send a test message
                channel = config.get("default_channel", "general")
                test_message = "🎉 ChatSphere bot has been successfully connected! I'm here to help."
                
                success = await slack_handler._send_bot_message(channel, test_message)
                if success:
                    integration_data["status"] = "active"
                else:
                    integration_data["status"] = "error"
                    integration_data["error"] = "Failed to send test message"
                    
            except Exception as e:
                logger.error(f"Error testing Slack integration: {str(e)}")
                integration_data["status"] = "error"
                integration_data["error"] = str(e)

            # Always update the integration in the database with the latest config
            if config.get("team_id"):
                await firestore_db.update_integration(
                    integration_data["id"],
                    {
                        "config": config,
                        "status": integration_data["status"],
                        "error": integration_data.get("error")
                    }
                )

            return integration_data

        elif integration_type == "website":
            domain = integration_data.get("config", {}).get("domain")
            if not domain:
                logger.warning("Missing domain for website integration")
                integration_data["status"] = "error"
                integration_data["config"]["error"] = "Domain is required"
            else:
                # Clean domain format
                domain = domain.replace("https://", "").replace("http://", "").strip("/")
                integration_data["config"]["domain"] = domain
                
                # Check if verification is needed
                if integration_data.get("status") == "pending":
                    # Check if we already have a verification token
                    token = integration_data.get("config", {}).get("verificationToken")
                    if not token:
                        # Generate new verification token
                        token = website_handler.generate_verification_token(domain)
                        integration_data["config"]["verificationToken"] = token
                    
                    # Get verification record details
                    verification_record = website_handler.get_verification_record(domain, token)
                    integration_data["config"]["verification"] = verification_record
                    
                    # Try to verify the domain
                    is_verified = await website_handler.verify_domain(domain, token)
                    if is_verified:
                        # Domain verified, now set up CNAME records
                        setup_details = await website_handler.setup_domain(domain)
                        integration_data["config"]["setup"] = setup_details
                        integration_data["status"] = "configuring"  # Waiting for CNAME setup
                    else:
                        # Still waiting for verification
                        integration_data["status"] = "pending"
                        
                elif integration_data.get("status") == "configuring":
                    # Check if CNAME is properly set up
                    is_setup = await website_handler.check_domain_setup(domain)
                    if is_setup:
                        integration_data["status"] = "active"
                    else:
                        # Still waiting for DNS propagation
                        integration_data["status"] = "configuring"
                        
                else:
                    # New integration, start verification process
                    token = website_handler.generate_verification_token(domain)
                    verification_record = website_handler.get_verification_record(domain, token)
                    integration_data["config"]["verificationToken"] = token
                    integration_data["config"]["verification"] = verification_record
                    integration_data["status"] = "pending"
                
        # Update the integration in the database
        await firestore_db.update_integration(
            integration_data["id"],
            {"status": integration_data["status"], "config": integration_data["config"]}
        )
        
        return integration_data
    except Exception as e:
        logger.error(f"Error processing {integration_type} integration: {str(e)}")
        logger.error(traceback.format_exc())
        integration_data["status"] = "error"
        integration_data["config"]["error"] = str(e)
        
        # Update the integration with error status
        await firestore_db.update_integration(
            integration_data["id"],
            {"status": "error", "config": integration_data["config"]}
        )
        
        return integration_data 