"""
Email utilities for sending confirmation emails and other notifications
Supports both Django's email backend (Gmail SMTP, console, etc.) and Brevo API
"""

import logging
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def send_email(to_email, subject, html_message, plain_message):
    """
    Send email using Django's configured email backend (Gmail SMTP, console, etc.)
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_message: HTML email body
        plain_message: Plain text email body (fallback)
    
    Returns:
        Tuple (success: bool, message_id or error: str)
    """
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email]
        )
        msg.attach_alternative(html_message, "text/html")
        result = msg.send(fail_silently=False)
        
        if result:
            logger.info(f"Email sent successfully to {to_email}")
            return True, "Email sent"
        else:
            logger.error(f"Failed to send email to {to_email}")
            return False, "Failed to send email"
            
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {str(e)}")
        return False, str(e)


def send_confirmation_email(user, request):
    """
    Send email confirmation link to new user
    
    Args:
        user: User object
        request: HTTP request object for building absolute URLs
    """
    try:
        # Get or create email confirmation record
        from .models import EmailConfirmation, EmailLog
        
        email_confirmation, created = EmailConfirmation.objects.get_or_create(
            user=user,
            defaults={'is_confirmed': False}
        )
        
        # Build confirmation link
        confirmation_url = request.build_absolute_uri(
            reverse('confirm_email', kwargs={'token': email_confirmation.token})
        )
        
        # Prepare email context
        context = {
            'user': user,
            'confirmation_url': confirmation_url,
            'expiry_hours': settings.EMAIL_CONFIRMATION_EXPIRY_HOURS,
        }
        
        # Render email template
        html_message = render_to_string('core/email_confirmation.html', context)
        plain_message = render_to_string('core/email_confirmation.txt', context)
        
        # Send email using Django's email backend
        success, response_id = send_email(
            user.email,
            "Confirm Your FitWell Account",
            html_message,
            plain_message
        )
        
        if success:
            # Log the email to database
            EmailLog.objects.create(
                user=user,
                email_address=user.email,
                email_type='confirmation',
                subject='Confirm Your FitWell Account',
                message_preview=plain_message[:500],
                is_sent=True,
            )
            logger.info(f"Confirmation email sent to {user.email}")
            return True
        else:
            raise Exception(f"Email backend error: {response_id}")
        
    except Exception as e:
        logger.error(f"Failed to send confirmation email to {user.email}: {str(e)}")
        
        # Log the failed email to database
        try:
            from .models import EmailLog
            EmailLog.objects.create(
                user=user,
                email_address=user.email,
                email_type='confirmation',
                subject='Confirm Your FitWell Account',
                message_preview='',
                is_sent=False,
                error_message=str(e),
            )
        except Exception as log_error:
            logger.error(f"Failed to log email error: {str(log_error)}")
        
        return False


def send_welcome_email(user):
    """
    Send welcome email after account creation
    
    Args:
        user: User object
    """
    try:
        from .models import EmailLog
        
        context = {
            'user': user,
        }
        
        html_message = render_to_string('core/email_welcome.html', context)
        plain_message = render_to_string('core/email_welcome.txt', context)
        
        # Send email using Django's email backend
        success, response_id = send_email(
            user.email,
            "Welcome to FitWell!",
            html_message,
            plain_message
        )
        
        if success:
            # Log the email to database
            EmailLog.objects.create(
                user=user,
                email_address=user.email,
                email_type='welcome',
                subject='Welcome to FitWell!',
                message_preview=plain_message[:500],
                is_sent=True,
            )
            logger.info(f"Welcome email sent to {user.email}")
            return True
        else:
            raise Exception(f"Email backend error: {response_id}")
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        
        # Log the failed email to database
        try:
            from .models import EmailLog
            EmailLog.objects.create(
                user=user,
                email_address=user.email,
                email_type='welcome',
                subject='Welcome to FitWell!',
                message_preview='',
                is_sent=False,
                error_message=str(e),
            )
        except Exception as log_error:
            logger.error(f"Failed to log email error: {str(log_error)}")
        
        return False
