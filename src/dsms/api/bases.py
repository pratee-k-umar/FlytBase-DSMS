"""
Base classes for API endpoints.
Sentry pattern: Consistent error handling and response formatting.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from dsms.utils.exceptions import DSMSError, NotFoundError, ValidationError


def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework.
    Provides consistent error response format.
    """
    from rest_framework.views import exception_handler
    
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Add error code to response
        error_data = {
            'error': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            'code': getattr(exc, 'code', 'error'),
            'status_code': response.status_code
        }
        response.data = error_data
    
    return response


class BaseEndpoint(APIView):
    """
    Base class for all API endpoints.
    Sentry pattern: All endpoints inherit from this for consistent behavior.
    
    Provides:
    - Standardized response helpers
    - Consistent error handling
    - Common permission patterns
    """
    
    def handle_exception(self, exc):
        """Handle custom DSMS exceptions"""
        if isinstance(exc, NotFoundError):
            return Response(
                {'error': str(exc), 'code': 'not_found'},
                status=status.HTTP_404_NOT_FOUND
            )
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc), 'code': 'validation_error'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if isinstance(exc, DSMSError):
            return Response(
                {'error': str(exc), 'code': exc.code},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)
    
    def respond(self, data=None, status_code=200):
        """Standardized success response"""
        return Response(data, status=status_code)
    
    def respond_created(self, data):
        """201 Created response"""
        return Response(data, status=status.HTTP_201_CREATED)
    
    def respond_no_content(self):
        """204 No Content response"""
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def respond_error(self, message, code='error', status_code=400):
        """Standardized error response"""
        return Response(
            {'error': message, 'code': code},
            status=status_code
        )
