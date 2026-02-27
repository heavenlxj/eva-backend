
from enum import Enum

class ErrorCode(Enum):
    def __init__(self, id, msg):
        self.id = id
        self.msg = msg

    # User
    WX_AUTH_INVALID = (100001, 'wechat auth invalid')
    # Client Type Error
    CLIENT_TYPE_INVALID = (100002, 'client type invalid')
    
    # Template Message Errors
    TEMPLATE_MESSAGE_SEND_FAILED = (200001, 'template message send failed')
    TEMPLATE_MESSAGE_USER_NOT_FOUND = (200002, 'no corresponding service account user found')
    TEMPLATE_MESSAGE_CHILD_USER_NOT_FOUND = (200003, 'no corresponding user found for child')
    TEMPLATE_MESSAGE_SERVICE_ERROR = (200004, 'template message service error')
    
    # Child Assets Errors
    CHILD_ASSET_NOT_FOUND = (300001, 'asset not found')
    CHILD_ASSET_ALREADY_PUBLISHED = (300002, 'asset already published')
    CHILD_ASSET_UPDATE_FAILED = (300003, 'failed to update public status, permission denied')
    
    # Internal Server Error
    INTERNAL_SERVER_ERROR = (100000, 'internal server error')
