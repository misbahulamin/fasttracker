from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Machine
from .utils import send_push_notification

@receiver(pre_save, sender=Machine)
def detect_status_change(sender, instance, **kwargs):
    if not instance.pk:
        # New machine being created; no status change
        instance._status_changed = False
        return

    try:
        previous = Machine.objects.get(pk=instance.pk)
        instance._status_changed = previous.status != instance.status
        instance._old_status = previous.status
        instance._new_status = instance.status
    except Machine.DoesNotExist:
        instance._status_changed = False

@receiver(post_save, sender=Machine)
def send_status_change_notification(sender, instance, created, **kwargs):
    if not created and getattr(instance, '_status_changed', False):
        old_status = instance._old_status
        new_status = instance._new_status
        machine_id = instance.machine_id
        model_number = instance.model_number
        line = instance.line
        last_problem = instance.last_problem
        
        # Retrieve location details
        line_name = line.name if line else 'Unknown line'
        operation_type = line.operation_type if line else 'operation'
        floor_no = line.floor.name if line else 'Unknown Floor'
        last_problem = last_problem if last_problem else 'Unknown Problem'

        if old_status == "active" and new_status == "broken":
            topic_name = "mechanics"
            title = f"🚨 A machine is broken down with {last_problem} in Floor: {floor_no}, Line: {line_name}, Operation: {operation_type}."
            body = (
                f"🔧 **Urgent Action Required**\n\n"
                f"📌 **Machine Details:**\n"
                f"    - ID: {machine_id}\n"
                f"    - Model: {model_number}\n"
                f"    - Status: ❌ Broken (was Active)\n"
                f"    - Issue: {last_problem}\n\n"
                f"📍 **Location Details:**\n"
                f"    - Floor: {floor_no}\n"
                f"    - Line: {line_name}\n"
                f"    - Operation Type: {operation_type}\n\n"
                "🚨 Immediate inspection and resolution are required to avoid further delays."
            )

        else:
            title = f"Machine {machine_id} Status Updated"
            topic_name = None
            body = (
                f"Machine {machine_id} ({model_number}) status changed from {old_status} to {new_status}.\n"
                f"Location details:\n"
                f"  - Operation: {operation_type}\n"
                f"  - Line: {line_name}\n"
                f"  - Floor: {floor_no}\n\n"
                "Please check the machine's current condition and ensure it's functioning as expected."
            )
        send_push_notification(title=title, body=body, topic=topic_name)
