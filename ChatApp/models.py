# pragma: no cover
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import hashlib
import json
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("analyst", "Analyst"),
    ]

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="analyst")
    totp_secret = models.CharField(max_length=32, blank=True, default="", help_text="Two-factor auth secret")
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Conversation(models.Model):
    user1 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='conversations_as_user1')
    user2 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='conversations_as_user2')
    retention_days = models.PositiveIntegerField(null=True, blank=True, help_text="Retention period override in days")
    legal_hold = models.BooleanField(default=False, help_text="Do not delete messages while enabled")

    def get_participants(self):
        return [self.user1, self.user2]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When to permanently delete this message")

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender} at {self.timestamp}"


class MessageReceipt(models.Model):
    """Tracks the latest message seen by a user in a conversation."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    last_seen_id = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "conversation")

    def __str__(self):
        return f"{self.user} in {self.conversation_id}: {self.last_seen_id}"


class Reaction(models.Model):
    emoji = models.CharField(max_length=10)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reactions")

    class Meta:
        unique_together = ("emoji", "user", "message")

    def __str__(self):
        return f"{self.emoji} by {self.user} on {self.message_id}"


class DeviceToken(models.Model):
    PLATFORM_CHOICES = [
        ("ios", "iOS"),
        ("android", "Android"),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="device_tokens")
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.platform}"


class AuditLog(models.Model):
    """Immutable record of important events."""
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=64)
    details = models.JSONField()
    previous_hash = models.CharField(max_length=64, blank=True)
    hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("AuditLog entries cannot be modified")
        if not self.timestamp:
            self.timestamp = timezone.now()
        last = AuditLog.objects.order_by("-id").first()
        self.previous_hash = last.hash if last else ""
        data = json.dumps(
            {
                "timestamp": self.timestamp.isoformat(),
                "user_id": self.user_id,
                "action": self.action,
                "details": self.details,
                "previous_hash": self.previous_hash,
            },
            sort_keys=True,
        )
        self.hash = hashlib.sha256(data.encode()).hexdigest()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditLog entries cannot be deleted")

    def __str__(self):
        return f"{self.timestamp} {self.action}"


class RetentionPolicy(models.Model):
    scope = models.CharField(max_length=255, unique=True)
    ttl_seconds = models.PositiveIntegerField()
    override_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.scope}: {self.ttl_seconds}s"


class ChatRoom(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(CustomUser, related_name="chat_rooms")

    def __str__(self):
        return self.name


class RoomMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender} in {self.room_id} at {self.timestamp}"


@receiver(post_save, sender=Message)
def log_message_sent(sender, instance, created, **kwargs):
    if created:
        from .audit import record_audit_event

        record_audit_event(
            user=instance.sender,
            action="message_sent",
            details={"message_id": instance.id, "conversation_id": instance.conversation_id},
        )
