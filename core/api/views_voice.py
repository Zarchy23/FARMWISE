# core/api/views_voice.py
# Voice Assistant API Views

from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import logging

from core.models_voice import (
    VoiceCommand, VoiceConversation, VoiceInteraction,
    VoicePreference, VoiceNotification, VoiceCommandHistory
)
from core.api.serializers_voice import (
    VoiceCommandSerializer, VoiceConversationSerializer, VoiceInteractionSerializer,
    VoicePreferenceSerializer, VoiceNotificationSerializer, VoiceCommandHistorySerializer
)
from core.services.voice_assistant_service import VoiceAssistantService

logger = logging.getLogger(__name__)


class VoiceCommandViewSet(viewsets.ReadOnlyModelViewSet):
    """View available voice commands"""
    queryset = VoiceCommand.objects.filter(is_active=True)
    serializer_class = VoiceCommandSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['command_type']
    search_fields = ['command_name', 'description']
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get commands grouped by type"""
        command_type = request.query_params.get('type')
        
        commands = VoiceCommand.objects.filter(
            is_active=True,
            command_type=command_type
        )
        
        serializer = self.get_serializer(commands, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def all_types(self, request):
        """Get all command types with examples"""
        types_data = {}
        for command_type in VoiceCommand.objects.values_list('command_type', flat=True).distinct():
            commands = VoiceCommand.objects.filter(
                command_type=command_type,
                is_active=True
            )
            types_data[command_type] = {
                'count': commands.count(),
                'examples': [cmd.command_name for cmd in commands[:3]]
            }
        
        return Response(types_data)


class VoiceConversationViewSet(viewsets.ModelViewSet):
    """Manage voice conversations"""
    serializer_class = VoiceConversationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'device_type']
    ordering_fields = ['started_at', 'ended_at']
    
    def get_queryset(self):
        """Filter conversations for current user"""
        return VoiceConversation.objects.filter(
            user=self.request.user
        ).order_by('-started_at')
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start a new voice conversation"""
        try:
            farm_id = request.data.get('farm_id')
            device_type = request.data.get('device_type', 'web')
            language = request.data.get('language', 'en')
            
            farm = None
            if farm_id:
                from core.models import Farm
                farm = Farm.objects.get(id=farm_id, owner=request.user)
            
            conversation = VoiceAssistantService.start_conversation(
                user=request.user,
                farm=farm,
                device_type=device_type,
                language=language
            )
            
            serializer = self.get_serializer(conversation)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            logger.error(f"Error starting conversation: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End a conversation"""
        conversation = self.get_object()
        user_satisfaction = request.data.get('satisfaction')
        feedback = request.data.get('feedback', '')
        
        success = VoiceAssistantService.end_conversation(
            conversation.id,
            user_satisfaction=user_satisfaction,
            feedback=feedback
        )
        
        if success:
            conversation.refresh_from_db()
            serializer = self.get_serializer(conversation)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Failed to end conversation'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active conversation for current user"""
        conversation = VoiceConversation.objects.filter(
            user=request.user,
            status='active'
        ).first()
        
        if conversation:
            serializer = self.get_serializer(conversation)
            return Response(serializer.data)
        else:
            return Response(
                {'message': 'No active conversation'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get interaction history for a conversation"""
        conversation = self.get_object()
        interactions = conversation.interactions.all().order_by('created_at')
        
        serializer = VoiceInteractionSerializer(interactions, many=True)
        return Response(serializer.data)


class VoiceInteractionViewSet(viewsets.ViewSet):
    """Handle voice command processing"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def process_command(self, request):
        """Process a voice command from transcribed text"""
        try:
            conversation_id = request.data.get('conversation_id')
            user_input = request.data.get('user_input')
            
            if not conversation_id or not user_input:
                return Response(
                    {'error': 'conversation_id and user_input are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Process the voice command
            result = VoiceAssistantService.process_voice_command(
                conversation_id=conversation_id,
                user_input_text=user_input,
                user=request.user
            )
            
            if 'error' in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error processing voice command: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def transcribe(self, request):
        """Handle audio transcription (would integrate with Azure/Google Speech-to-Text)"""
        # This endpoint would receive audio and call the speech-to-text service
        # For now, return a placeholder
        
        return Response({
            'message': 'Audio transcription should be handled by client-side Web Speech API or server-side Azure Speech Services',
            'note': 'Send transcribed text to /process_command endpoint'
        })


class VoicePreferenceViewSet(viewsets.ViewSet):
    """Manage voice assistant preferences"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Get current user's voice preferences"""
        pref, created = VoicePreference.objects.get_or_create(
            user=request.user
        )
        serializer = VoicePreferenceSerializer(pref)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """Update voice preferences"""
        try:
            pref, created = VoicePreference.objects.get_or_create(
                user=request.user
            )
            
            serializer = VoicePreferenceSerializer(
                pref,
                data=request.data,
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class VoiceNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """View voice notifications"""
    serializer_class = VoiceNotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter notifications for current user"""
        return VoiceNotification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)


class VoiceCommandHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """View voice command execution history"""
    serializer_class = VoiceCommandHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter history for current user"""
        return VoiceCommandHistory.objects.filter(
            user=self.request.user
        ).order_by('-executed_at')
    
    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """Mark command as helpful"""
        history = self.get_object()
        history.user_helpful = True
        history.save()
        
        serializer = self.get_serializer(history)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get command usage statistics"""
        history = self.get_queryset()
        
        stats = {
            'total_commands': history.count(),
            'successful': history.filter(success=True).count(),
            'failed': history.filter(success=False).count(),
            'helpful': history.filter(user_helpful=True).count(),
            'success_rate': (
                history.filter(success=True).count() / history.count() * 100
                if history.exists() else 0
            )
        }
        
        return Response(stats)


class VoiceAssistantDashboardView(views.APIView):
    """Dashboard for voice assistant usage and stats"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get voice assistant dashboard data"""
        try:
            # Recent conversations
            conversations = VoiceConversation.objects.filter(
                user=request.user
            ).order_by('-started_at')[:5]
            
            # Preferences
            pref, _ = VoicePreference.objects.get_or_create(
                user=request.user
            )
            
            # Statistics
            all_history = VoiceCommandHistory.objects.filter(
                user=request.user
            )
            
            total_conversations = VoiceConversation.objects.filter(
                user=request.user
            ).count()
            
            return Response({
                'recent_conversations': VoiceConversationSerializer(conversations, many=True).data,
                'preferences': VoicePreferenceSerializer(pref).data,
                'statistics': {
                    'total_conversations': total_conversations,
                    'total_commands': all_history.count(),
                    'successful_rate': (
                        all_history.filter(success=True).count() / all_history.count() * 100
                        if all_history.exists() else 0
                    ),
                    'helpful_commands': all_history.filter(user_helpful=True).count(),
                }
            })
        
        except Exception as e:
            logger.error(f"Error loading voice dashboard: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
