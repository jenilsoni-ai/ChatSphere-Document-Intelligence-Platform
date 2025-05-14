from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any, Optional

from ..db.firebase import FirestoreDB, FirebaseAuth
from ..models.user import UserCreate, UserLogin, UserResponse, PasswordReset

router = APIRouter()
firebase_auth = FirebaseAuth()
firestore_db = FirestoreDB()

# OAuth2 password bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        # Create user in Firebase Auth
        user_id = await firebase_auth.create_user(user_data.email, user_data.password)
        
        # Create user document in Firestore
        user_dict = {
            "uid": user_id,
            "email": user_data.email,
            "displayName": user_data.display_name,
            "role": "user"
        }
        await firestore_db.create_user(user_dict)
        
        # Generate token
        token = await firebase_auth.create_custom_token(user_id)
        
        return {
            "uid": user_id,
            "email": user_data.email,
            "displayName": user_data.display_name,
            "token": token
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=UserResponse)
async def login_user(user_data: UserLogin):
    """Login a user"""
    try:
        # Authenticate user with Firebase
        user_id, email = await firebase_auth.sign_in_with_email_password(user_data.email, user_data.password)
        
        # Get user data from Firestore
        user = await firestore_db.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update last login timestamp
        await firestore_db.update_user(user_id, {"lastLogin": firestore_db.server_timestamp()})
        
        # Generate token
        token = await firebase_auth.create_custom_token(user_id)
        
        return {
            "uid": user_id,
            "email": email,
            "displayName": user.get("displayName", ""),
            "token": token
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/logout")
async def logout_user(token: str = Depends(oauth2_scheme)):
    """Logout a user"""
    try:
        # Revoke token
        await firebase_auth.revoke_token(token)
        return {"message": "Logout successful"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logout failed: {str(e)}"
        )

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Send password reset email"""
    try:
        await firebase_auth.send_password_reset_email(reset_data.email)
        return {"message": "Password reset email sent"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password reset failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user data"""
    try:
        # Verify token and get user ID
        user_id = await firebase_auth.verify_token(token)
        
        # Get user data from Firestore
        user = await firestore_db.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "uid": user_id,
            "email": user.get("email", ""),
            "displayName": user.get("displayName", ""),
            "token": token
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )