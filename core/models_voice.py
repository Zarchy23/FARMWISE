# core/models_voice.py
# Voice Assistant Models for FarmWise
# Handles voice commands, conversations, and text-to-speech

from django.db import models
from django.conf import settings
from django.utils import timezone
import json


class VoiceCommand(models.Model):
    """Predefined voice commands for agriculture"""
    
    COMMAND_TYPE = [
        ('weather', 'Weather Inquiry'),
        ('prices', 'Price Check'),
        ('pest', 'Pest Report'),
        ('yield', 'Yield Prediction'),
        ('task', 'Farm Task'),
        ('reminder', 'Set Reminder'),
        ('alert', 'Alert Check'),
        ('advice', 'Farming Advice'),
        ('other', 'Other'),
    ]
    
    command_name = models.CharField(max_length=100)
    command_type = models.CharField(max_length=20, choices=COMMAND_TYPE)
    description = models.TextField()
    
    # Voice variants (same command, different ways to say it)
    voice_variants = models.JSONField(default=list, help_text="List of ways to say this command")
    
    # Handler configuration
    handler_function = models.CharField(max_length=200, help_text="Python function to handle this command")
    requires_farm_context = models.BooleanField(default=False)
    requires_parameters = models.JSONField(default=dict, help_text="Required parameters and types")
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'voice_commands'
        unique_together = ['command_name', 'command_type']
    
    def __str__(self):
        return f"{self.command_name} ({self.command_type})"


class VoiceConversation(models.Model):
    """Session-based voice conversations"""
    
    STATUS = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='voice_conversations')
    farm = models.ForeignKey('core.Farm', on_delete=models.SET_NULL, null=True, blank=True, related_name='voice_conversations')
    
    status = models.CharField(max_length=20, choices=STATUS, default='active')
    
    # Conversation metadata
    device_type = models.CharField(max_length=50, default='web')  # web, mobile, alexa, etc.
    language = models.CharField(max_length=10, default='en')
    
    # Context
    context_data = models.JSONField(default=dict, help_text="Conversation context for multi-turn interactions")
    
    # Statistics
    message_count = models.IntegerField(default=0)
    command_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    
    # Duration
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.IntegerField(blank=True, null=True)
    
    # Satisfaction
    user_satisfaction = models.IntegerField(blank=True, null=True, help_text="1-5 rating")
    feedback_text = models.TextField(blank=True)
    
    class Meta:
        db_table = 'voice_conversations'
        indexes = [
            models.Index(fields=['user', 'status', 'started_at']),
        ]
    
    def __str__(self):
        return f"Voice session - {self.user.first_name} ({self.started_at})"


class VoiceInteraction(models.Model):
    """Individual voice message in a conversation"""
    
    INTERACTION_TYPE = [
        ('command', 'Voice Command'),
        ('query', 'Question/Query'),
        ('response', 'System Response'),
        ('confirmation', 'Confirmation'),
        ('error', 'Error Message'),
    ]
    
    conversation = models.ForeignKey(VoiceConversation, on_delete=models.CASCADE, related_name='interactions')
    
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPE)
    
    # User input
    user_input_text = models.TextField(help_text="User's spoken text (after transcription)")
    user_input_audio = models.FileField(upload_to='voice_audio/user/', blank=True, null=True)
    
    # System response
    system_response_text = models.TextField(help_text="System's response text")
    system_response_audio = models.FileField(upload_to='voice_audio/system/', blank=True, null=True)
    
    # Processing
    recognized_command = models.ForeignKey(VoiceCommand, on_delete=models.SET_NULL, null=True, blank=True)
    confidence_score = models.FloatField(default=0.0, help_text="0-1 confidence in command recognition")
    
    # Extracted parameters
    extracted_parameters = models.JSONField(default=dict)
    
    # Status
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    # Metadata
    duration_seconds = models.FloatField(blank=True, null=True)
    processing_time_ms = models.IntegerField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'voice_interactions'
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.interaction_type} - {self.user_input_text[:50]}"


class VoicePreference(models.Model):
    """User voice assistant preferences"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='voice_preferences')
    
    # Voice settings
    is_enabled = models.BooleanField(default=True)
    preferred_language = models.CharField(max_length=10, default='en')
    speech_rate = models.FloatField(default=1.0)  # 0.5-2.0
    volume_level = models.IntegerField(default=70)  # 0-100
    
    # TTS provider
    TTS_PROVIDER = [
        ('azure', 'Azure Speech Services'),
        ('google', 'Google Cloud Text-to-Speech'),
        ('local', 'Local Browser (Web Speech)'),
    ]
    tts_provider = models.CharField(max_length=20, choices=TTS_PROVIDER, default='local')
    
    # STT provider
    STT_PROVIDER = [
        ('azure', 'Azure Speech-to-Text'),
        ('google', 'Google Cloud Speech-to-Text'),
        ('local', 'Local Browser (Web Speech)'),
    ]
    stt_provider = models.CharField(max_length=20, choices=STT_PROVIDER, default='local')
    
    # Features
    auto_read_responses = models.BooleanField(default=True)
    show_transcriptions = models.BooleanField(default=True)
    save_audio_logs = models.BooleanField(default=False)
    
    # Notifications
    enable_voice_alerts = models.BooleanField(default=True)
    alert_volume = models.IntegerField(default=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'voice_preferences'
    
    def __str__(self):
        return f"Voice settings - {self.user.first_name}"


class VoiceNotification(models.Model):
    """Voice notifications sent to users"""
    
    NOTIFICATION_TYPE = [
        ('alert', 'Important Alert'),
        ('reminder', 'Reminder'),
        ('suggestion', 'Suggestion'),
        ('update', 'System Update'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='voice_notifications')
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Audio
    audio_file = models.FileField(upload_to='voice_notifications/', blank=True, null=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_played = models.BooleanField(default=False)
    
    # Scheduling
    scheduled_for = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    
    # Priority
    PRIORITY = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY, default='normal')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'voice_notifications'
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.title}"


class VoiceCommandHistory(models.Model):
    """History of executed voice commands for learning"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='voice_command_history')
    command = models.ForeignKey(VoiceCommand, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Execution details
    command_text = models.TextField()
    parameters = models.JSONField(default=dict)
    
    # Outcome
    success = models.BooleanField(default=True)
    result_summary = models.TextField(blank=True)
    
    # Feedback
    user_helpful = models.BooleanField(blank=True, null=True)
    user_notes = models.TextField(blank=True)
    
    executed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'voice_command_history'
        indexes = [
            models.Index(fields=['user', 'executed_at']),
        ]
    
    def __str__(self):
        return f"{self.user.first_name} - {self.command_text[:50]}"
