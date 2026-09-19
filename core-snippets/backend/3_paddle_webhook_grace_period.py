import hmac
import hashlib
import json
import logging
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

logger = logging.getLogger(__name__)

# Note: This is an isolated snippet from the Brio AI backend demonstrating 
# secure webhook validation and Grace Period logic for Paddle billing events.

@csrf_exempt # External ingress bypass
def paddle_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    secret = settings.PADDLE_WEBHOOK_SECRET
    signature_header = request.headers.get('Paddle-Signature', '')

    # 1. Cryptographic validation of the webhook origin
    parts = dict(part.split('=') for part in signature_header.split(';') if '=' in part)
    ts = parts.get('ts')
    h1 = parts.get('h1')

    if not ts or not h1:
        return HttpResponse(status=403)

    payload = f"{ts}:{request.body.decode('utf-8')}"
    expected_hash = hmac.new(secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, h1):
        logger.warning("Paddle Webhook: Signature verification failed.")
        return HttpResponse(status=403)

    # 2. Event Payload Parsing
    try:
        payload_data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        logger.error("Paddle Webhook: Invalid JSON payload.")
        return HttpResponse(status=400)

    event_type = payload_data.get('event_type', '')

    # 3. Subscription State Machine (Business Logic)
    if event_type.startswith('subscription.'):
        data = payload_data.get('data') or {}
        status = data.get('status')
        
        # Mapping Paddle customer/subscription ID to internal user omitted for brevity
        user_profile = get_user_profile(data) 
        
        if user_profile:
            if status == 'active':
                user_profile.is_premium = True
                user_profile.subscription_status = 'active'

            elif status == 'canceled':
                # Grace Period Logic: Maintain access until the paid period ends
                if user_profile.premium_expires_at and user_profile.premium_expires_at > timezone.now():
                    user_profile.is_premium = True
                    user_profile.subscription_status = 'canceled'
                    logger.info(f"Webhook: Grace Period started for user {user_profile.id}")
                else:
                    user_profile.is_premium = False
                    user_profile.subscription_status = 'canceled'
                    logger.info(f"Webhook: Premium revoked for user {user_profile.id}")
            else:
                user_profile.is_premium = False
                user_profile.subscription_status = status

            user_profile.save()

    return HttpResponse(status=200)

def get_user_profile(data):
    # Mocked data access layer
    pass