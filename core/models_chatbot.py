# core/models_chatbot.py
# AI Chatbot Models for Agricultural Guidance

from django.db import models
from django.conf import settings


class ChatIntent(models.Model):
    """Predefined intents for chatbot NLU"""
    INTENT_CATEGORIES = [
        ('crop_advice', 'Crop Advice'),
        ('pest_disease', 'Pest & Disease'),
        ('weather', 'Weather & Climate'),
        ('market', 'Market & Prices'),
        ('soil', 'Soil & Fertilizer'),
        ('irrigation', 'Irrigation'),
        ('harvesting', 'Harvesting'),
        ('storage', 'Storage & Preservation'),
        ('financial', 'Financial Planning'),
        ('general', 'General Question'),
    ]
    
    intent_name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=INTENT_CATEGORIES)
    keywords = models.JSONField(default=list, help_text='List of keywords that trigger this intent')
    description = models.TextField()
    response_template = models.TextField(help_text='Template for generating responses')
    confidence_threshold = models.FloatField(default=0.7)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'intent_name']
    
    def __str__(self):
        return f"{self.intent_name} ({self.category})"


class ChatSession(models.Model):
    """Represents a chat conversation session"""
    SESSION_STATUS = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sessions')
    farm = models.ForeignKey('core.Farm', on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_sessions')
    title = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='active')
    language = models.CharField(max_length=10, default='en')
    context_data = models.JSONField(default=dict, help_text='Session context (crop type, region, etc)')
    message_count = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    user_satisfaction = models.IntegerField(null=True, blank=True, help_text='1-5 rating')
    feedback = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"


class ChatMessage(models.Model):
    """Individual messages in a chat session"""
    MESSAGE_TYPE = [
        ('user', 'User Message'),
        ('bot', 'Bot Response'),
        ('system', 'System Message'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE)
    content = models.TextField()
    intent = models.ForeignKey(ChatIntent, on_delete=models.SET_NULL, null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True, help_text='NLU confidence (0-1)')
    metadata = models.JSONField(default=dict, help_text='Additional message context')
    is_helpful = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.message_type} - {self.content[:50]}"


class ChatResponse(models.Model):
    """Stored responses for common questions"""
    question = models.CharField(max_length=500, unique=True)
    answer = models.TextField()
    category = models.CharField(max_length=50)
    keywords = models.JSONField(default=list)
    usage_count = models.IntegerField(default=0)
    avg_satisfaction = models.FloatField(default=0.0)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-usage_count']
    
    def __str__(self):
        return self.question[:100]


class ChatFeedback(models.Model):
    """Feedback on chatbot responses for improvement"""
    FEEDBACK_RATING = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('neutral', 'Neutral'),
        ('poor', 'Poor'),
        ('unhelpful', 'Unhelpful'),
    ]
    
    message = models.OneToOneField(ChatMessage, on_delete=models.CASCADE, related_name='feedback')
    rating = models.CharField(max_length=20, choices=FEEDBACK_RATING)
    comment = models.TextField(blank=True)
    tags = models.JSONField(default=list, help_text='Tags for categorizing feedback')
    user_submitted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.message.session.user.username} - {self.rating}"


class ChatStatistics(models.Model):
    """Aggregated chatbot statistics"""
    date = models.DateField(auto_now_add=True, unique=True)
    total_sessions = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    avg_messages_per_session = models.FloatField(default=0.0)
    avg_satisfaction = models.FloatField(default=0.0)
    most_common_intent = models.CharField(max_length=100, blank=True)
    unique_users = models.IntegerField(default=0)
    resolved_queries = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Stats for {self.date}"
