# core/api/serializers_voice.py
# Voice Assistant API Serializers

from rest_framework import serializers
from core.models_voice import (
    VoiceCommand, VoiceConversation, VoiceInteraction,
    VoicePreference, VoiceNotification, VoiceCommandHistory
)


class VoiceCommandSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceCommand
        fields = [
            'id', 'command_name', 'command_type', 'description',
            'voice_variants', 'requires_parameters', 'is_active'
        ]


class VoiceInteractionSerializer(serializers.ModelSerializer):
    command_name = serializers.CharField(source='recognized_command.command_name', read_only=True)
    
    class Meta:
        model = VoiceInteraction
        fields = [
            'id', 'user_input_text', 'system_response_text', 'command_name',
            'confidence_score', 'success', 'error_message', 'processing_time_ms',
            'created_at'
        ]
        read_only_fields = ['created_at', 'processing_time_ms']


class VoiceConversationSerializer(serializers.ModelSerializer):
    interactions = VoiceInteractionSerializer(many=True, read_only=True)
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = VoiceConversation
        fields = [
            'id', 'status', 'farm_name', 'device_type', 'language',
            'message_count', 'command_count', 'error_count',
            'started_at', 'ended_at', 'duration_seconds',
            'user_satisfaction', 'feedback_text', 'interactions'
        ]
        read_only_fields = ['started_at', 'ended_at', 'duration_seconds']


class VoicePreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoicePreference
        fields = [
            'is_enabled', 'preferred_language', 'speech_rate', 'volume_level',
            'tts_provider', 'stt_provider', 'auto_read_responses',
            'show_transcriptions', 'save_audio_logs', 'enable_voice_alerts',
            'alert_volume'
        ]


class VoiceNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceNotification
        fields = [
            'id', 'notification_type', 'title', 'message',
            'is_read', 'is_played', 'priority', 'created_at'
        ]
        read_only_fields = ['created_at']


class VoiceCommandHistorySerializer(serializers.ModelSerializer):
    command_name = serializers.CharField(source='command.command_name', read_only=True)
    
    class Meta:
        model = VoiceCommandHistory
        fields = [
            'id', 'command_name', 'command_text', 'success',
            'result_summary', 'user_helpful', 'executed_at'
        ]
        read_only_fields = ['executed_at']
