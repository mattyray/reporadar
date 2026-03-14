"""Celery task for async outreach message generation."""

import os

import anthropic
from celery import shared_task


@shared_task(bind=True, max_retries=1)
def generate_outreach_message(self, message_id: str):
    """Generate an outreach message via Claude API."""
    from .models import OutreachMessage
    from .views import _build_prompt, _parse_subject

    try:
        outreach = OutreachMessage.objects.select_related(
            "organization", "contact"
        ).get(pk=message_id)
    except OutreachMessage.DoesNotExist:
        return {"status": "error", "detail": "Message not found"}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        outreach.status = "failed"
        outreach.error = "Anthropic API key not configured on server."
        outreach.save(update_fields=["status", "error"])
        return {"status": "failed"}

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": _build_prompt(outreach.context_used),
                }
            ],
        )
        raw_text = message.content[0].text

        # Parse subject line from email responses
        subject = ""
        body = raw_text
        if outreach.message_type == "email":
            subject, body = _parse_subject(raw_text)

        outreach.subject = subject
        outreach.body = body
        outreach.status = "completed"
        outreach.save(update_fields=["subject", "body", "status"])

        return {"status": "completed", "message_id": str(message_id)}

    except Exception as e:
        outreach.status = "failed"
        outreach.error = str(e)
        outreach.save(update_fields=["status", "error"])
        raise self.retry(exc=e)
