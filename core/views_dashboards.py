# core/views_dashboards.py
# Dashboard view functions that render HTML templates
# Replaces API endpoints with server-side rendered views

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# ============================================================
# OFFLINE DASHBOARD
# ============================================================

@login_required
def offline_dashboard(request):
    """Offline mode dashboard - render HTML instead of JSON"""
    try:
        # Import here to avoid circular imports
        from .services.offline_service import OfflineService
        from .models_offline import OfflineSyncLog
        from .api.serializers_offline import OfflineSyncLogSerializer
        
        # Get offline data
        pref = OfflineService.get_or_create_preference(request.user)
        cache_stats = OfflineService.get_cache_statistics(request.user)
        offline_analytics = OfflineService.get_offline_analytics(request.user)
        pending_syncs = OfflineService.get_pending_syncs(request.user)
        
        # Get recent sync logs
        sync_logs = OfflineSyncLog.objects.filter(
            user=request.user
        ).order_by('-sync_timestamp')[:5]
        
        context = {
            'offline_enabled': pref.enable_offline_mode,
            'sync_mode': pref.get_sync_mode_display(),
            'cache_stats': cache_stats,
            'analytics': offline_analytics,
            'pending_syncs_count': pending_syncs.count(),
            'recent_syncs': OfflineSyncLogSerializer(sync_logs, many=True).data,
            'cache_features': {
                'voice': pref.enable_voice_offline,
                'chat': pref.enable_chat_offline,
                'market_data': pref.enable_market_data_offline
            },
            'background_sync': pref.background_sync_enabled,
            'sync_on_wifi_only': pref.sync_on_wifi_only
        }
        
        return render(request, 'offline/dashboard.html', context)
    
    except Exception as e:
        logger.error(f"Error loading offline dashboard: {str(e)}")
        context = {
            'error': f"Error loading offline dashboard: {str(e)}",
            'offline_enabled': False,
            'sync_mode': 'Unknown',
            'cache_stats': {},
            'analytics': {},
            'pending_syncs_count': 0,
            'recent_syncs': [],
            'cache_features': {},
            'background_sync': False,
            'sync_on_wifi_only': False
        }
        return render(request, 'offline/dashboard.html', context)


# ============================================================
# MARKET DASHBOARD
# ============================================================

@login_required
def market_dashboard(request):
    """Market dashboard - display marketplace listings and analytics"""
    try:
        from .models import ProductListing
        
        # Get marketplace data
        my_listings = ProductListing.objects.filter(seller__owner=request.user).order_by('-created_at')[:5]
        all_listings = ProductListing.objects.filter(status='active').order_by('-created_at')[:10]
        total_listings = ProductListing.objects.filter(status='active').count()
        
        context = {
            'my_listings': my_listings,
            'all_listings': all_listings,
            'total_listings': total_listings,
        }
        
        return render(request, 'market/dashboard.html', context)
    
    except Exception as e:
        logger.error(f"Error loading market dashboard: {str(e)}")
        context = {'error': f"Error loading market dashboard: {str(e)}"}
        return render(request, 'market/dashboard.html', context)


# ============================================================
# VOICE ASSISTANT DASHBOARD
# ============================================================

@login_required
def voice_dashboard(request):
    """Voice assistant dashboard"""
    try:
        from .models_voice import VoiceConversation, VoiceCommandHistory
        
        # Get voice data
        recent_conversations = VoiceConversation.objects.filter(
            user=request.user
        ).order_by('-started_at')[:10]
        
        total_commands = VoiceCommandHistory.objects.filter(
            user=request.user
        ).count()
        
        successful_commands = VoiceCommandHistory.objects.filter(
            user=request.user,
            user_helpful=True
        ).count()
        
        # Calculate success rate
        success_rate = 0
        if total_commands > 0:
            success_rate = (successful_commands / total_commands) * 100
        
        context = {
            'recent_conversations': recent_conversations,
            'total_commands': total_commands,
            'successful_commands': successful_commands,
            'success_rate': success_rate,
        }
        
        return render(request, 'voice/dashboard.html', context)
    
    except Exception as e:
        logger.error(f"Error loading voice dashboard: {str(e)}")
        context = {'error': f"Error loading voice dashboard: {str(e)}"}
        return render(request, 'voice/dashboard.html', context)


@login_required
def voice_commands(request):
    """Available voice commands"""
    try:
        from .models_voice import VoiceCommand
        
        # Get all active voice commands
        commands = VoiceCommand.objects.filter(is_active=True).order_by('command_type', 'command_name')
        
        # Group by command type
        grouped_commands = {}
        for command in commands:
            if command.command_type not in grouped_commands:
                grouped_commands[command.command_type] = []
            grouped_commands[command.command_type].append(command)
        
        context = {
            'grouped_commands': grouped_commands,
            'total_commands': commands.count(),
        }
        
        return render(request, 'voice/commands.html', context)
    
    except Exception as e:
        logger.error(f"Error loading voice commands: {str(e)}")
        context = {'error': f"Error loading voice commands: {str(e)}"}
        return render(request, 'voice/commands.html', context)


@login_required
def voice_history(request):
    """Voice command history for current user"""
    try:
        from .models_voice import VoiceCommandHistory
        
        # Get command history for current user
        history = VoiceCommandHistory.objects.filter(
            user=request.user
        ).order_by('-executed_at')[:50]
        
        context = {
            'history': history,
            'total_count': VoiceCommandHistory.objects.filter(user=request.user).count(),
        }
        
        return render(request, 'voice/history.html', context)
    
    except Exception as e:
        logger.error(f"Error loading voice history: {str(e)}")
        context = {'error': f"Error loading voice history: {str(e)}"}
        return render(request, 'voice/history.html', context)


@login_required
def voice_preferences(request):
    """Voice assistant preferences"""
    try:
        from .models_voice import VoicePreference
        
        # Get or create preferences for current user
        preferences, created = VoicePreference.objects.get_or_create(
            user=request.user,
            defaults={
                'preferred_language': 'en',
                'is_enabled': True,
                'auto_read_responses': True,
            }
        )
        
        if request.method == 'POST':
            # Update preferences
            preferences.preferred_language = request.POST.get('preferred_language', 'en')
            preferences.is_enabled = request.POST.get('is_enabled') == 'on'
            preferences.auto_read_responses = request.POST.get('auto_read_responses') == 'on'
            preferences.speech_rate = float(request.POST.get('speech_rate', 1.0))
            preferences.volume_level = int(request.POST.get('volume_level', 70))
            preferences.show_transcriptions = request.POST.get('show_transcriptions') == 'on'
            preferences.save()
            return render(request, 'voice/preferences.html', {
                'preferences': preferences,
                'success': True,
            })
        
        context = {
            'preferences': preferences,
        }
        
        return render(request, 'voice/preferences.html', context)
    
    except Exception as e:
        logger.error(f"Error loading voice preferences: {str(e)}")
        context = {'error': f"Error loading voice preferences: {str(e)}"}
        return render(request, 'voice/preferences.html', context)


@login_required
def voice_interface(request):
    """Voice assistant interface for recording and playback"""
    try:
        from .models_voice import VoicePreference
        
        # Get user preferences - use simpler approach for faster loading
        try:
            preferences = VoicePreference.objects.get(user=request.user)
        except VoicePreference.DoesNotExist:
            # Create minimal preferences if they don't exist
            preferences = VoicePreference.objects.create(
                user=request.user,
                preferred_language='en',
                is_enabled=True,
                auto_read_responses=True,
            )
        
        context = {
            'preferences': preferences,
        }
        
        return render(request, 'voice/interface.html', context)
    
    except Exception as e:
        logger.error(f"Error loading voice interface: {str(e)}")
        # Return basic interface even if preferences fail
        context = {'error': f"Error loading voice interface: {str(e)}"}
        return render(request, 'voice/interface.html', context)


@csrf_exempt
def api_voice_process(request):
    """API endpoint to process voice commands"""
    logger.info("=== API VOICE PROCESS START ===")
    logger.info(f"Request method: {request.method}")
    
    if request.method != 'POST':
        logger.warning("Non-POST request received")
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    try:
        import json
        from .services.voice_assistant_service import VoiceAssistantService
        from .models_voice import VoiceConversation, VoiceCommandHistory, VoicePreference
        
        # Log the raw request body for debugging
        logger.info(f"Request body: {request.body}")
        
        try:
            data = json.loads(request.body)
            logger.info(f"Parsed JSON data: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)
        
        command_text = data.get('command', '').strip()
        
        logger.info(f"Extracted command: '{command_text}'")
        
        if not command_text:
            logger.warning("No command provided in request")
            return JsonResponse({'error': 'No command provided'}, status=400)
        
        # Get user preferences (for authentication, we'd normally use @login_required but this is API)
        # For now, we'll process without user context or you can add authentication
        user = getattr(request, 'user', None)
        logger.info(f"User: {user}, Authenticated: {user.is_authenticated if user else False}")
        
        # Process the voice command
        logger.info("Calling VoiceAssistantService.process_command...")
        try:
            result = VoiceAssistantService.process_command(
                command_text=command_text,
                user=user
            )
            logger.info(f"Result from service: {result}")
        except Exception as e:
            logger.error(f"Exception in VoiceAssistantService.process_command: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'error': f'Service error: {str(e)}'}, status=500)
        
        logger.info(f"Checking result success: {result.get('success')}")
        
        # Log the command regardless of success
        if user and user.is_authenticated:
            try:
                VoiceCommandHistory.objects.create(
                    user=user,
                    command_text=command_text,
                    success=result.get('success', True),
                    result_summary=result.get('response', '')[:500],
                    parameters=result.get('parameters', {})
                )
                logger.info("Command logged to history")
            except Exception as e:
                logger.error(f"Error logging command history: {e}")
        
        # Get user preference for auto-speak
        speak_response = False
        if user and user.is_authenticated:
            try:
                pref = VoicePreference.objects.get(user=user)
                speak_response = pref.auto_read_responses
            except VoicePreference.DoesNotExist:
                pass
        
        # Return response even if command wasn't recognized (200 OK, not 400)
        response_data = {
            'success': result.get('success', False),
            'response': result.get('response', 'Command processed'),
            'speak_response': speak_response,
            'parameters': result.get('parameters', {}),
            'command_type': result.get('command_type')
        }
        logger.info(f"Returning response: {response_data}")
        logger.info("=== API VOICE PROCESS END ===")
        return JsonResponse(response_data)
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing voice command: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================
# CHATBOT DASHBOARD
# ============================================================

@login_required
def chatbot_dashboard(request):
    """AI Chatbot dashboard"""
    try:
        from core.models_chatbot import ChatSession, ChatMessage
        
        # Get chat data
        recent_sessions = ChatSession.objects.filter(
            user=request.user
        ).order_by('-started_at')[:10]
        
        total_messages = ChatMessage.objects.filter(
            session__user=request.user
        ).count()
        
        context = {
            'recent_sessions': recent_sessions,
            'total_messages': total_messages,
        }
        
        return render(request, 'chat/dashboard.html', context)
    
    except ImportError:
        # Models don't exist - provide empty data
        context = {
            'recent_sessions': [],
            'total_messages': 0,
            'error': 'Chat models not available'
        }
        return render(request, 'chat/dashboard.html', context)
    
    except Exception as e:
        logger.error(f"Error loading chatbot dashboard: {str(e)}")
        context = {
            'recent_sessions': [],
            'total_messages': 0,
            'error': f"Error loading chatbot dashboard: {str(e)}"
        }
        return render(request, 'chat/dashboard.html', context)


@login_required
def chat_interface(request):
    """AI Chatbot chat interface - start a new chat or continue existing"""
    try:
        from core.models_chatbot import ChatSession, ChatMessage
        
        # Get or create a new chat session
        if request.method == 'POST':
            # Create new session
            session = ChatSession.objects.create(
                user=request.user,
                title=request.POST.get('title', 'New Chat'),
                status='active'
            )
            return render(request, 'chat/interface.html', {
                'session': session,
                'messages': [],
            })
        
        # Get most recent active session or create new one
        recent_session = ChatSession.objects.filter(
            user=request.user,
            status='active'
        ).order_by('-started_at').first()
        
        if not recent_session:
            recent_session = ChatSession.objects.create(
                user=request.user,
                title='Chat Session',
                status='active'
            )
        
        # Get messages for this session
        messages = ChatMessage.objects.filter(
            session=recent_session
        ).order_by('created_at')
        
        context = {
            'session': recent_session,
            'messages': messages,
        }
        
        return render(request, 'chat/interface.html', context)
    
    except Exception as e:
        logger.error(f"Error loading chat interface: {str(e)}")
        context = {'error': f"Error loading chat interface: {str(e)}"}
        return render(request, 'chat/interface.html', context)


@login_required
def api_chat_message(request):
    """API endpoint to send and receive chat messages with image support"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    try:
        from core.models_chatbot import ChatSession, ChatMessage
        from core.services.chatbot_service import ChatbotService
        
        # Handle both JSON and multipart form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Multipart form data (with image)
            session_id = request.POST.get('session_id')
            user_message = request.POST.get('message', '').strip()
            image_file = request.FILES.get('image')
        else:
            # JSON data (without image)
            import json
            data = json.loads(request.body)
            session_id = data.get('session_id')
            user_message = data.get('message', '').strip()
            image_file = None
        
        if not session_id:
            return JsonResponse({'error': 'Missing session_id'}, status=400)
        
        if not user_message and not image_file:
            return JsonResponse({'error': 'Message or image required'}, status=400)
        
        # Get session
        session = ChatSession.objects.get(id=session_id, user=request.user)
        
        # Process message using ChatbotService with image support
        result = ChatbotService.process_message(
            session_id, 
            user_message, 
            user=request.user,
            image_file=image_file
        )
        
        if 'error' in result:
            return JsonResponse({'error': result['error']}, status=500)
        
        # Get all messages for the session
        messages = ChatMessage.objects.filter(
            session=session
        ).order_by('created_at').values('id', 'message_type', 'content', 'created_at')
        
        response_data = {
            'success': True,
            'response': result['response'],
            'intent': result.get('intent'),
            'confidence': result.get('confidence'),
            'messages': list(messages),
            'session_id': session_id
        }
        
        # Add image analysis if available
        if result.get('image_analysis'):
            response_data['image_analysis'] = result['image_analysis']
        
        return JsonResponse(response_data)
    
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'Chat session not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in chat API: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================
# LOCATION/GPS DASHBOARD
# ============================================================

@login_required
def location_dashboard(request):
    """Location and GPS mapping dashboard"""
    try:
        from .models import Farm
        from .models_location import FarmField
        
        # Get location data
        farms = Farm.objects.filter(owner=request.user).prefetch_related('location_fields')
        total_fields = FarmField.objects.filter(farm__owner=request.user).count()
        
        context = {
            'farms': farms,
            'total_fields': total_fields,
        }
        
        return render(request, 'location/dashboard.html', context)
    
    except Exception as e:
        logger.error(f"Error loading location dashboard: {str(e)}")
        context = {'error': f"Error loading location dashboard: {str(e)}"}
        return render(request, 'location/dashboard.html', context)


# ============================================================
# DISEASE DIAGNOSIS DASHBOARD
# ============================================================

@login_required
def disease_dashboard(request):
    """Disease diagnosis and treatment dashboard"""
    try:
        from .models import DiseaseDiagnosis, DiseaseHistory
        
        # Get disease data
        recent_diagnoses = DiseaseDiagnosis.objects.filter(
            farm__owner=request.user
        ).order_by('-created_at')[:10]
        
        context = {
            'recent_diagnoses': recent_diagnoses,
        }
        
        return render(request, 'disease/dashboard.html', context)
    
    except Exception as e:
        logger.error(f"Error loading disease dashboard: {str(e)}")
        context = {'error': f"Error loading disease dashboard: {str(e)}"}
        return render(request, 'disease/dashboard.html', context)
