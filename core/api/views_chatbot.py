# core/api/views_chatbot.py
# Chatbot API Views

from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import logging

from core.models_chatbot import (
    ChatIntent, ChatSession, ChatMessage, ChatResponse, ChatFeedback, ChatStatistics
)
from core.api.serializers_chatbot import (
    ChatIntentSerializer, ChatSessionSerializer, ChatSessionDetailSerializer,
    ChatMessageSerializer, ChatResponseSerializer, ChatFeedbackSerializer, ChatStatisticsSerializer
)
from core.services.chatbot_service import ChatbotService

logger = logging.getLogger(__name__)


class ChatIntentViewSet(viewsets.ReadOnlyModelViewSet):
    """View available chat intents for NLU"""
    queryset = ChatIntent.objects.filter(is_active=True)
    serializer_class = ChatIntentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category']
    search_fields = ['intent_name', 'keywords']
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get intents grouped by category"""
        category = request.query_params.get('category')
        
        intents = ChatIntent.objects.filter(
            is_active=True,
            category=category
        )
        
        serializer = self.get_serializer(intents, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def all_categories(self, request):
        """Get all categories with example intents"""
        categories_data = {}
        for cat_value, cat_label in ChatIntent._meta.get_field('category').choices:
            intents = ChatIntent.objects.filter(
                category=cat_value,
                is_active=True
            )
            categories_data[cat_label] = {
                'count': intents.count(),
                'examples': [intent.intent_name for intent in intents[:3]]
            }
        
        return Response(categories_data)


class ChatSessionViewSet(viewsets.ModelViewSet):
    """Manage chat sessions"""
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'language']
    ordering_fields = ['started_at', 'ended_at']
    
    def get_queryset(self):
        """Filter sessions for current user"""
        return ChatSession.objects.filter(
            user=self.request.user
        ).order_by('-started_at')
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve action"""
        if self.action == 'retrieve':
            return ChatSessionDetailSerializer
        return ChatSessionSerializer
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start a new chat session"""
        try:
            farm_id = request.data.get('farm_id')
            language = request.data.get('language', 'en')
            
            farm = None
            if farm_id:
                from core.models import Farm
                farm = Farm.objects.get(id=farm_id, owner=request.user)
            
            session = ChatbotService.start_session(
                user=request.user,
                farm=farm,
                language=language
            )
            
            serializer = self.get_serializer(session)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            logger.error(f"Error starting chat session: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End a chat session"""
        session = self.get_object()
        user_satisfaction = request.data.get('satisfaction')
        feedback = request.data.get('feedback', '')
        
        success = ChatbotService.end_session(
            session.id,
            user_satisfaction=user_satisfaction,
            feedback=feedback
        )
        
        if success:
            session.refresh_from_db()
            serializer = self.get_serializer(session)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Failed to end session'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active session for current user"""
        session = ChatSession.objects.filter(
            user=request.user,
            status='active'
        ).first()
        
        if session:
            serializer = self.get_serializer(session)
            return Response(serializer.data)
        else:
            return Response(
                {'message': 'No active session'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages in a session"""
        session = self.get_object()
        messages = session.messages.all().order_by('created_at')
        
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)


class ChatMessageViewSet(viewsets.ViewSet):
    """Handle sending and receiving chat messages"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def send(self, request):
        """Send a message in a chat session"""
        try:
            session_id = request.data.get('session_id')
            user_input = request.data.get('message')
            
            if not session_id or not user_input:
                return Response(
                    {'error': 'session_id and message are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Process the message
            result = ChatbotService.process_message(
                session_id=session_id,
                user_input=user_input,
                user=request.user
            )
            
            if 'error' in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def feedback(self, request):
        """Submit feedback on a bot response"""
        try:
            message_id = request.data.get('message_id')
            rating = request.data.get('rating')
            comment = request.data.get('comment', '')
            tags = request.data.get('tags', [])
            
            if not message_id or not rating:
                return Response(
                    {'error': 'message_id and rating are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            feedback = ChatbotService.save_message_feedback(
                message_id=message_id,
                rating=rating,
                comment=comment,
                tags=tags
            )
            
            if feedback:
                serializer = ChatFeedbackSerializer(feedback)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'Failed to save feedback'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Error saving feedback: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search for responses to a query"""
        query = request.query_params.get('q')
        
        if not query:
            return Response(
                {'error': 'q parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        responses = ChatbotService.search_responses(query)
        serializer = ChatResponseSerializer(responses, many=True)
        return Response(serializer.data)


class ChatResponseViewSet(viewsets.ReadOnlyModelViewSet):
    """View stored chat responses"""
    queryset = ChatResponse.objects.filter(is_approved=True).order_by('-usage_count')
    serializer_class = ChatResponseSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category']
    search_fields = ['question', 'answer', 'keywords']
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get responses grouped by category"""
        category = request.query_params.get('category')
        
        responses = ChatResponse.objects.filter(
            category=category,
            is_approved=True
        ).order_by('-usage_count')
        
        serializer = self.get_serializer(responses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def most_helpful(self, request):
        """Get most helpful responses by satisfaction"""
        responses = ChatResponse.objects.filter(
            is_approved=True
        ).order_by('-avg_satisfaction')[:10]
        
        serializer = self.get_serializer(responses, many=True)
        return Response(serializer.data)


class ChatStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """View chatbot statistics"""
    queryset = ChatStatistics.objects.all().order_by('-date')
    serializer_class = ChatStatisticsSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ['date', 'total_sessions', 'avg_satisfaction']
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's statistics"""
        from django.utils import timezone
        today = timezone.now().date()
        
        stats = ChatStatistics.objects.filter(date=today).first()
        
        if stats:
            serializer = self.get_serializer(stats)
            return Response(serializer.data)
        else:
            return Response(
                {'message': 'No statistics available for today'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate and store today's statistics"""
        try:
            stats = ChatbotService.calculate_session_statistics()
            
            if stats:
                serializer = self.get_serializer(stats)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'Failed to calculate statistics'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ChatbotDashboardView(views.APIView):
    """Dashboard for chatbot usage and analytics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get chatbot dashboard data"""
        try:
            # Recent sessions
            sessions = ChatSession.objects.filter(
                user=request.user
            ).order_by('-started_at')[:5]
            
            # Session statistics
            total_sessions = ChatSession.objects.filter(
                user=request.user
            ).count()
            
            active_sessions = ChatSession.objects.filter(
                user=request.user,
                status='active'
            ).count()
            
            total_messages = ChatMessage.objects.filter(
                session__user=request.user
            ).count()
            
            # Intent breakdown
            intent_stats = {}
            intents = ChatMessage.objects.filter(
                session__user=request.user,
                intent__isnull=False
            ).values('intent__intent_name').distinct()
            
            for intent_data in intents:
                intent_name = intent_data['intent__intent_name']
                count = ChatMessage.objects.filter(
                    session__user=request.user,
                    intent__intent_name=intent_name
                ).count()
                intent_stats[intent_name] = count
            
            # Satisfaction metrics
            feedback_count = ChatFeedback.objects.filter(
                message__session__user=request.user
            ).count()
            
            satisfied_feedback = ChatFeedback.objects.filter(
                message__session__user=request.user,
                rating__in=['excellent', 'good']
            ).count()
            
            satisfaction_rate = (
                (satisfied_feedback / feedback_count * 100)
                if feedback_count > 0 else 0
            )
            
            return Response({
                'recent_sessions': ChatSessionSerializer(sessions, many=True).data,
                'statistics': {
                    'total_sessions': total_sessions,
                    'active_sessions': active_sessions,
                    'total_messages': total_messages,
                    'satisfaction_rate': satisfaction_rate,
                    'feedback_count': feedback_count
                },
                'intent_breakdown': intent_stats,
                'top_intents': sorted(intent_stats.items(), key=lambda x: x[1], reverse=True)[:5]
            })
        
        except Exception as e:
            logger.error(f"Error loading chatbot dashboard: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
