"""
Base Model Classes
Provides common functionality for all MongoEngine documents.
"""

from datetime import datetime
from mongoengine import Document, DateTimeField


class BaseDocument(Document):
    """
    Abstract base class for all DSMS documents.
    Provides common timestamp fields and metadata.
    """
    
    created_at = DateTimeField(default=datetime.utcnow, required=True)
    updated_at = DateTimeField(default=datetime.utcnow, required=True)
    
    meta = {
        'abstract': True,
        'strict': False,
    }
    
    def save(self, *args, **kwargs):
        """Override save to update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def to_dict(self):
        """Convert document to dictionary, handling ObjectId serialization."""
        data = self.to_mongo().to_dict()
        data['id'] = str(data.pop('_id'))
        return data
