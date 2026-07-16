# core/api/serializers_chatbot.py
# DRF Serializers for Chatbot API

from rest_framework import serializers
from core.models_chatbot import (
    ChatIntent, ChatSession, ChatMessage, ChatResponse, ChatFeedback, ChatStatistics
)


class ChatIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatIntent
        fields = [
            'id', 'intent_name', 'category', 'keywords', 'description',
            'confidence_threshold', 'is_active', 'created_at'
        ]


class ChatMessageSerializer(serializers.ModelSerializer):
    intent_name = serializers.CharField(source='intent.intent_name', read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'message_type', 'content', 'intent', 'intent_name',
            'confidence_score', 'metadata', 'is_helpful', 'created_at'
        ]


class ChatFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatFeedback
        fields = [
            'id', 'message', 'rating', 'comment', 'tags',
            'user_submitted', 'created_at'
        ]


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'status', 'language', 'context_data',
            'message_count', 'started_at', 'ended_at', 'user_satisfaction',
            'feedback', 'farm', 'farm_name', 'messages'
        ]


class ChatSessionSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'status', 'language', 'message_count',
            'started_at', 'ended_at', 'user_satisfaction', 'farm', 'farm_name'
        ]


class ChatResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatResponse
        fields = [
            'id', 'question', 'answer', 'category', 'keywords',
            'usage_count', 'avg_satisfaction', 'is_approved', 'created_at'
        ]


class ChatStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatStatistics
        fields = [
            'id', 'date', 'total_sessions', 'total_messages',
            'avg_messages_per_session', 'avg_satisfaction', 'most_common_intent',
            'unique_users', 'resolved_queries'
        ]
