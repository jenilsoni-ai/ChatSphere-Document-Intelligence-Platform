from fastapi import UploadFile
import os
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
from typing import Dict, Any, List, Optional
from datetime import datetime
import tempfile
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..core.config import settings
import logging
import traceback

logger = logging.getLogger(__name__)

class FirebaseApp:
    _instance = None
    _initialized = False

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if not FirebaseApp._initialized:
            self.initialize_firebase()
            FirebaseApp._initialized = True

    def initialize_firebase(self):
        """Initialize Firebase Admin SDK with credentials"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                })
            self.app = firebase_admin.get_app()
            self.db = firestore.client()
            self.bucket = storage.bucket()
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise

# Initialize Firebase singleton
firebase_app = FirebaseApp.get_instance()

# Firestore operations
class FirestoreDB:
    def __init__(self):
        self.app = firebase_app.app
        self.db = firebase_app.db
    
    # User operations
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user in Firestore"""
        user_ref = self.db.collection('users').document(user_data['uid'])
        user_ref.set({
            **user_data,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'lastLogin': firestore.SERVER_TIMESTAMP
        })
        return user_data['uid']
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data from Firestore"""
        user_ref = self.db.collection('users').document(user_id)
        user = user_ref.get()
        if user.exists:
            return user.to_dict()
        return None
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Update user data in Firestore"""
        user_ref = self.db.collection('users').document(user_id)
        user_ref.update({
            **user_data,
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        return True
    
    # Chatbot operations
    async def create_chatbot(self, chatbot_data: Dict[str, Any]) -> str:
        """Create a new chatbot in Firestore"""
        # Get the ID from the chatbot_data or generate a new one if not provided
        chatbot_id = chatbot_data.get('id', None)
        if chatbot_id:
            # Use the provided ID
            chatbot_ref = self.db.collection('chatbots').document(chatbot_id)
        else:
            # Generate a new ID if not provided
            chatbot_ref = self.db.collection('chatbots').document()
            chatbot_id = chatbot_ref.id
            chatbot_data['id'] = chatbot_id
        
        # Set the data
        chatbot_ref.set({
            **chatbot_data,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        return chatbot_id
    
    async def get_chatbot(self, chatbot_id: str) -> Optional[Dict[str, Any]]:
        """Get chatbot data from Firestore"""
        chatbot_ref = self.db.collection('chatbots').document(chatbot_id)
        chatbot = chatbot_ref.get()
        if chatbot.exists:
            return chatbot.to_dict()
        return None
    
    async def update_chatbot(self, chatbot_id: str, chatbot_data: Dict[str, Any]) -> bool:
        """Update chatbot data in Firestore"""
        chatbot_ref = self.db.collection('chatbots').document(chatbot_id)
        chatbot_ref.update({
            **chatbot_data,
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        return True
    
    async def delete_chatbot(self, chatbot_id: str) -> bool:
        """Delete chatbot from Firestore"""
        chatbot_ref = self.db.collection('chatbots').document(chatbot_id)
        chatbot_ref.delete()
        return True
    
    async def list_chatbots(self, owner_id: str) -> List[Dict[str, Any]]:
        """List all chatbots for a user"""
        chatbots = self.db.collection('chatbots').where('ownerId', '==', owner_id).stream()
        return [chatbot.to_dict() for chatbot in chatbots]
    
    # Document operations
    async def create_document(self, data: Dict[str, Any]) -> str:
        """Create a new document in Firestore, using provided ID if available."""
        try:
            # Add timestamps if not already present (though API layer adds them)
            if 'createdAt' not in data:
                data['createdAt'] = datetime.utcnow().isoformat()
            if 'updatedAt' not in data:
                data['updatedAt'] = datetime.utcnow().isoformat()
            
            document_id = data.get('id')

            if document_id:
                # Use the provided ID
                doc_ref = self.db.collection('documents').document(document_id)
            else:
                # Auto-generate ID if not provided
                doc_ref = self.db.collection('documents').document()
                document_id = doc_ref.id
                data['id'] = document_id # Ensure ID is in the data being set

            # Set the data in Firestore
            doc_ref.set(data, merge=True) # Use merge=True to avoid overwriting existing fields if re-uploading?
            
            # Return the document ID used
            return document_id
            
        except Exception as e:
            logger.error(f"Error creating/updating document {data.get('id', '')} in Firestore: {str(e)}", exc_info=True)
            raise
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID"""
        try:
            doc_ref = self.db.collection('documents').document(document_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting document from Firestore: {str(e)}")
            raise
    
    async def update_document(self, document_id: str, data: Dict[str, Any]) -> None:
        """Update a document by ID"""
        try:
            data['updatedAt'] = datetime.utcnow().isoformat()
            doc_ref = self.db.collection('documents').document(document_id)
            doc_ref.update(data)
        except Exception as e:
            logger.error(f"Error updating document in Firestore: {str(e)}")
            raise
    
    async def delete_document(self, document_id: str) -> None:
        """Delete a document by ID"""
        try:
            doc_ref = self.db.collection('documents').document(document_id)
            doc_ref.delete()
        except Exception as e:
            logger.error(f"Error deleting document from Firestore: {str(e)}")
            raise
    
    async def list_documents(self, owner_id: str) -> list[Dict[str, Any]]:
        """List all documents for a specific owner
        
        Args:
            owner_id: The ID of the document owner
            
        Returns:
            List of documents owned by the user
        """
        try:
            docs = self.db.collection('documents').where('ownerId', '==', owner_id).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error listing documents from Firestore: {str(e)}")
            raise
    
    # Chat session operations
    async def create_chat_session(self, session_data: Dict[str, Any]) -> str:
        """Create a new chat session in Firestore"""
        session_ref = self.db.collection('chatSessions').document()
        session_id = session_ref.id
        session_ref.set({
            **session_data,
            'id': session_id,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP,
            'messages': []
        })
        return session_id
    
    async def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get chat session data from Firestore"""
        session_ref = self.db.collection('chatSessions').document(session_id)
        session = session_ref.get()
        if session.exists:
            return session.to_dict()
        return None
    
    async def add_chat_message(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Add a message to a chat session"""
        session_ref = self.db.collection('chatSessions').document(session_id)
        session_ref.update({
            'messages': firestore.ArrayUnion([{
                **message,
                'timestamp': firestore.SERVER_TIMESTAMP
            }]),
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        return True
    
    async def list_chat_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """List all chat sessions for a user"""
        sessions = self.db.collection('chatSessions').where('userId', '==', user_id).stream()
        return [session.to_dict() for session in sessions]
    
    async def list_chat_sessions_by_chatbot(self, chatbot_id: str) -> List[Dict[str, Any]]:
        """List all chat sessions for a specific chatbot"""
        sessions = self.db.collection('chatSessions').where('chatbotId', '==', chatbot_id).stream()
        return [session.to_dict() for session in sessions]
    
    async def delete_chat_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        session_ref = self.db.collection('chatSessions').document(session_id)
        session_ref.delete()
        return True
    
    # Integration methods
    async def list_integrations(self, user_id):
        """List all integrations for a user"""
        try:
            integrations_ref = self.db.collection("integrations")
            query = integrations_ref.where("userId", "==", user_id)
            integrations_docs = query.stream()
            
            integrations = []
            for doc in integrations_docs:
                integration = doc.to_dict()
                integrations.append(integration)
                
            return integrations
        except Exception as e:
            logger.error(f"Error listing integrations: {str(e)}")
            logger.error(traceback.format_exc())
            raise e
    
    async def create_integration(self, integration_data):
        """Create a new integration"""
        try:
            integration_id = integration_data.get("id")
            if not integration_id:
                raise ValueError("Integration ID is required")
                
            integration_ref = self.db.collection("integrations").document(integration_id)
            integration_ref.set(integration_data)
            
            return integration_data
        except Exception as e:
            logger.error(f"Error creating integration: {str(e)}")
            logger.error(traceback.format_exc())
            raise e
    
    async def get_integration(self, integration_id):
        """Get an integration by ID"""
        try:
            integration_ref = self.db.collection("integrations").document(integration_id)
            integration_doc = integration_ref.get()
            
            if not integration_doc.exists:
                return None
                
            return integration_doc.to_dict()
        except Exception as e:
            logger.error(f"Error getting integration: {str(e)}")
            logger.error(traceback.format_exc())
            raise e
    
    async def update_integration(self, integration_id, update_data):
        """Update an integration"""
        try:
            integration_ref = self.db.collection("integrations").document(integration_id)
            integration_ref.update(update_data)
            
            return True
        except Exception as e:
            logger.error(f"Error updating integration: {str(e)}")
            logger.error(traceback.format_exc())
            raise e
    
    async def delete_integration(self, integration_id):
        """Delete an integration"""
        try:
            integration_ref = self.db.collection("integrations").document(integration_id)
            integration_ref.delete()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting integration: {str(e)}")
            logger.error(traceback.format_exc())
            raise e

    # User settings methods
    async def get_user_settings(self, user_id: str):
        """Get user settings from Firestore"""
        try:
            settings_ref = self.db.collection("settings").document(user_id)
            settings_doc = settings_ref.get()
            
            if not settings_doc.exists:
                return None
                
            return settings_doc.to_dict()
        except Exception as e:
            logger.error(f"Error getting user settings: {str(e)}")
            logger.error(traceback.format_exc())
            raise e
    
    async def create_user_settings(self, settings_data):
        """Create user settings in Firestore"""
        try:
            user_id = settings_data.get("userId")
            if not user_id:
                raise ValueError("User ID is required for settings")
                
            settings_ref = self.db.collection("settings").document(user_id)
            settings_ref.set(settings_data)
            
            return settings_data
        except Exception as e:
            logger.error(f"Error creating user settings: {str(e)}")
            logger.error(traceback.format_exc())
            raise e
    
    async def update_user_settings(self, user_id, update_data):
        """Update user settings in Firestore"""
        try:
            settings_ref = self.db.collection("settings").document(user_id)
            settings_ref.update(update_data)
            
            return True
        except Exception as e:
            logger.error(f"Error updating user settings: {str(e)}")
            logger.error(traceback.format_exc())
            raise e

    async def list_integrations_by_query(self, field_path: str, op_string: str, value: Any) -> List[Dict[str, Any]]:
        """List integrations by a specific query"""
        try:
            integrations_ref = self.db.collection("integrations")
            query = integrations_ref.where(field_path, op_string, value)
            integrations_docs = query.stream()
            
            integrations = []
            for doc in integrations_docs:
                integration = doc.to_dict()
                integrations.append(integration)
                
            return integrations
        except Exception as e:
            logger.error(f"Error listing integrations by query: {str(e)}")
            logger.error(traceback.format_exc())
            raise e

    async def get_document_stats(self) -> Dict[str, Any]:
        """Get document statistics
        
        Returns:
            Dictionary with document statistics
        """
        try:
            # Get all documents
            documents_ref = self.db.collection('documents')
            docs = await documents_ref.get()
            
            # Count by status
            status_counts = {
                "total": 0,
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
                "other": 0
            }
            
            for doc in docs:
                status_counts["total"] += 1
                doc_data = doc.to_dict()
                status = doc_data.get('processingStatus', 'unknown')
                
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts["other"] += 1
            
            # Count documents with vectors
            docs_with_vectors = 0
            docs_without_vectors = 0
            
            for doc in docs:
                doc_data = doc.to_dict()
                vector_ids = doc_data.get('vectorIds', [])
                
                if vector_ids and len(vector_ids) > 0:
                    docs_with_vectors += 1
                else:
                    docs_without_vectors += 1
            
            return {
                "status_counts": status_counts,
                "vector_stats": {
                    "with_vectors": docs_with_vectors,
                    "without_vectors": docs_without_vectors
                }
            }
        except Exception as e:
            logger.error(f"Error getting document stats: {e}")
            raise

# Firebase Storage operations
class FirebaseStorage:
    def __init__(self):
        self.app = firebase_app.app
        self.bucket = firebase_app.bucket
        self.logger = logging.getLogger(__name__)
    
    async def upload_file(self, file: UploadFile, document_id: str, user_id: str) -> int:
        """Upload a file to Firebase Storage"""
        temp_file = None
        try:
            self.logger.info(f"Starting Firebase upload for user {user_id}")
            
            # Validate file
            if not file or not file.filename:
                raise ValueError("No file provided")
                
            # Create the storage path
            storage_path = f"documents/{user_id}/{document_id}/{file.filename}"
            self.logger.info(f"Storage path: {storage_path}")
            
            # Read file content first
            content = await file.read()
            file_size = len(content)
            self.logger.info(f"Read file content, size: {file_size} bytes")
            
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file_path = temp_file.name
            self.logger.info(f"Created temporary file: {temp_file_path}")
            
            # Write content to temp file
            temp_file.write(content)
            temp_file.flush()
            temp_file.close()  # Close the file handle explicitly
            
            try:
                # Create blob and upload
                blob = self.bucket.blob(storage_path)
                self.logger.info("Created blob reference")
                
                # Upload the file
                blob.upload_from_filename(
                    temp_file_path,
                    content_type=file.content_type
                )
                self.logger.info("Upload completed")
                
                # Make the file publicly accessible
                blob.make_public()
                self.logger.info(f"File is now public at: {blob.public_url}")
                
            finally:
                # Clean up temp file
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                        self.logger.info("Temporary file cleaned up")
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to clean up temporary file: {cleanup_error}")
            
            # Reset file pointer for potential future reads
            await file.seek(0)
            
            return file_size
            
        except Exception as e:
            self.logger.error(f"Firebase upload failed: {str(e)}")
            # Attempt final cleanup if temp file exists
            if temp_file:
                try:
                    temp_file_path = temp_file.name
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                except Exception:
                    pass  # Ignore cleanup errors in error handler
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to Firebase Storage: {str(e)}"
            )
    
    async def download_file(self, source_path: str) -> str:
        """Download a file from Firebase Storage, preserving the extension."""
        try:
            blob = self.bucket.blob(source_path)
            if not blob.exists():
                 logger.error(f"Blob does not exist at source path: {source_path}")
                 raise FileNotFoundError(f"File not found in storage at {source_path}")
            
            # Get the original filename and extension from the source path
            original_filename = os.path.basename(source_path)
            _, extension = os.path.splitext(original_filename)
            logger.info(f"Original filename: {original_filename}, Extension: {extension}")

            # Create a named temporary file with the correct suffix (extension)
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
                logger.info(f"Downloading to temporary file: {temp_file.name}")
                blob.download_to_filename(temp_file.name)
                logger.info(f"Download complete for {source_path}")
                return temp_file.name
        except Exception as e:
             logger.error(f"Failed to download file from {source_path}: {e}", exc_info=True)
             raise
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from Firebase Storage"""
        blob = self.bucket.blob(file_path)
        blob.delete()
        return True

# Firebase Authentication operations
class FirebaseAuth:
    def __init__(self):
        self.app = firebase_app.app
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify Firebase ID token"""
        try:
            # Add 60 seconds of clock skew tolerance to account for minor time differences
            decoded_token = auth.verify_id_token(token, clock_skew_seconds=60)
            logging.debug(f"Token verified successfully for user: {decoded_token.get('uid', 'unknown')}")
            return decoded_token
        except Exception as e:
            logging.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )

    async def create_user(self, email: str, password: str, display_name: str) -> Dict[str, Any]:
        """Create a new user in Firebase Authentication"""
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )
        return {
            'uid': user.uid,
            'email': user.email,
            'displayName': user.display_name
        }
    
    async def get_user(self, uid: str) -> Dict[str, Any]:
        """Get user data from Firebase Authentication"""
        user = auth.get_user(uid)
        return {
            'uid': user.uid,
            'email': user.email,
            'displayName': user.display_name,
            'emailVerified': user.email_verified
        }
    
    async def update_user(self, uid: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data in Firebase Authentication"""
        user = auth.update_user(
            uid,
            **user_data
        )
        return {
            'uid': user.uid,
            'email': user.email,
            'displayName': user.display_name
        }
    
    async def delete_user(self, uid: str) -> bool:
        """Delete user from Firebase Authentication"""
        auth.delete_user(uid)
        return True

# Create instances to be imported by other modules
firestore_db = FirestoreDB()
storage = FirebaseStorage()
firebase_auth = FirebaseAuth()

# Export the instances
__all__ = ['firestore_db', 'storage', 'firebase_auth']