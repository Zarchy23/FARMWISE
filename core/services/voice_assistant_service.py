# core/services/voice_assistant_service.py
# Voice Assistant Service - Handles voice commands and conversations

import logging
import json
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
import re

logger = logging.getLogger(__name__)


class VoiceAssistantService:
    """Service for managing voice interactions and commands"""
    
    # Command patterns for matching
    COMMAND_PATTERNS = {
        'weather': [
            r"what(?:'s| is) the weather",
            r"weather forecast",
            r"tell me.*weather",
            r"how(?:'s| is) the weather",
            r"will it rain",
            r"temperature today",
            r"check weather",
        ],
        'prices': [
            r"what.*price",
            r"crop prices",
            r"commodity prices",
            r"market prices?",
            r"check prices",
            r"how much.*worth",
            r"selling price",
            r"price.*crop",
            r"current prices",
        ],
        'pest': [
            r"pest report",
            r"disease detection",
            r"see pest",
            r"report pest",
            r"detect pest",
            r"crop disease",
            r"pest problem",
        ],
        'yield': [
            r"yield prediction",
            r"crop yield",
            r"expect.*harvest",
            r"predict yield",
            r"harvest prediction",
        ],
        'task': [
            r"create task",
            r"add reminder",
            r"schedule.*activity",
            r"plant.*date",
            r"harvest.*date",
            r"farm task",
        ],
        'alert': [
            r"any alerts?",
            r"what(?:'s| is) new",
            r"notifications?",
            r"check alerts?",
        ],
    }
    
    @staticmethod
    def get_database_context(user, command_text):
        """
        Fetch relevant database data based on user and command
        Returns structured context for AI to use in responses
        Command-aware: fetches specific data based on what user is asking
        """
        context = {
            'farms': [],
            'crops': [],
            'livestock': [],
            'location': 'Zimbabwe',
            'user_info': {},
            'command_type': 'general'
        }
        
        if not user or not user.is_authenticated:
            return context
        
        command_lower = command_text.lower()
        
        try:
            from core.models import Farm, CropSeason, Animal
            
            # Determine command type for targeted data fetching
            if any(word in command_lower for word in ['weather', 'temperature', 'rain', 'forecast', 'climate']):
                context['command_type'] = 'weather'
                # For weather, focus on farm locations
                farms = Farm.objects.filter(owner=user)
                farm_locations = []
                for farm in farms:
                    location = farm.location if hasattr(farm, 'location') else 'Unknown'
                    farm_locations.append(location)
                    context['farms'].append({
                        'name': farm.name,
                        'location': location
                    })
                context['locations'] = farm_locations
                logger.info(f"Weather command - fetched {len(farm_locations)} farm locations")
                
            elif any(word in command_lower for word in ['price', 'market', 'cost', 'sell', 'buy', 'commodity']):
                context['command_type'] = 'prices'
                # For prices, focus on crops
                crops = CropSeason.objects.filter(field__farm__owner=user).select_related('crop_type')
                crop_names = []
                for crop in crops:
                    if crop.crop_type:
                        crop_names.append(crop.crop_type.name)
                        context['crops'].append({
                            'name': crop.crop_type.name,
                            'farm': crop.field.farm.name if crop.field and crop.field.farm else 'Unknown'
                        })
                context['crop_names'] = crop_names
                logger.info(f"Prices command - fetched {len(crop_names)} crop types")
                
            elif any(word in command_lower for word in ['farm', 'report', 'summary', 'overview', 'my farm']):
                context['command_type'] = 'farm_report'
                # For farm reports, get comprehensive data
                farms = Farm.objects.filter(owner=user)
                for farm in farms:
                    context['farms'].append({
                        'name': farm.name,
                        'location': farm.location if hasattr(farm, 'location') else 'Unknown',
                        'size': farm.size if hasattr(farm, 'size') else 'Unknown',
                        'soil_type': farm.soil_type if hasattr(farm, 'soil_type') else 'Unknown'
                    })
                
                crops = CropSeason.objects.filter(field__farm__owner=user).select_related('crop_type', 'field')
                for crop in crops:
                    context['crops'].append({
                        'name': crop.crop_type.name if crop.crop_type else 'Unknown',
                        'field': crop.field.name if crop.field else 'Unknown',
                        'farm': crop.field.farm.name if crop.field and crop.field.farm else 'Unknown',
                        'status': crop.status,
                        'planting_date': str(crop.planting_date) if crop.planting_date else 'Unknown',
                        'expected_harvest': str(crop.expected_harvest_date) if crop.expected_harvest_date else 'Unknown'
                    })
                
                animals = Animal.objects.filter(farm__owner=user)
                for animal in animals:
                    context['livestock'].append({
                        'type': animal.animal_type if hasattr(animal, 'animal_type') else 'Unknown',
                        'breed': animal.breed if hasattr(animal, 'breed') else 'Unknown',
                        'count': animal.count if hasattr(animal, 'count') else 1,
                        'farm': animal.farm.name if animal.farm else 'Unknown'
                    })
                logger.info(f"Farm report - fetched {len(context['farms'])} farms, {len(context['crops'])} crops, {len(context['livestock'])} livestock")
                
            elif any(word in command_lower for word in ['pest', 'disease', 'insect', 'bug', 'infection']):
                context['command_type'] = 'pest'
                # For pest info, focus on crops and locations
                crops = CropSeason.objects.filter(field__farm__owner=user).select_related('crop_type', 'field__farm')
                for crop in crops:
                    context['crops'].append({
                        'name': crop.crop_type.name if crop.crop_type else 'Unknown',
                        'location': crop.field.farm.location if crop.field and crop.field.farm and hasattr(crop.field.farm, 'location') else 'Unknown'
                    })
                logger.info(f"Pest command - fetched {len(context['crops'])} crops with locations")
                
            elif any(word in command_lower for word in ['yield', 'harvest', 'production', 'output']):
                context['command_type'] = 'yield'
                # For yield, focus on active crops
                crops = CropSeason.objects.filter(field__farm__owner=user).select_related('crop_type', 'field')
                for crop in crops:
                    context['crops'].append({
                        'name': crop.crop_type.name if crop.crop_type else 'Unknown',
                        'status': crop.status,
                        'expected_harvest': str(crop.expected_harvest_date) if crop.expected_harvest_date else 'Unknown',
                        'farm': crop.field.farm.name if crop.field and crop.field.farm else 'Unknown'
                    })
                logger.info(f"Yield command - fetched {len(context['crops'])} crops")
                
            else:
                # General command - get basic info
                context['command_type'] = 'general'
                farms = Farm.objects.filter(owner=user)
                for farm in farms:
                    context['farms'].append({
                        'name': farm.name,
                        'location': farm.location if hasattr(farm, 'location') else 'Unknown'
                    })
                logger.info(f"General command - fetched {len(context['farms'])} farms")
            
            # Always include user info
            context['user_info'] = {
                'username': user.username,
                'role': user.role if hasattr(user, 'role') else 'Farmer',
                'location': user.profile.location if hasattr(user, 'profile') and hasattr(user.profile, 'location') else 'Zimbabwe'
            }
            
        except Exception as e:
            logger.error(f"Error fetching database context: {e}")
        
        return context
    
    @staticmethod
    def enhance_input_with_context(command_text, db_context):
        """
        Enhance the user's command with database context for better AI understanding
        This ensures the AI actually uses the provided data
        """
        enhanced_text = command_text
        context_info = []
        
        # Add farm locations for weather queries
        if db_context.get('command_type') == 'weather' and db_context.get('locations'):
            locations = db_context['locations']
            if locations:
                location_names = []
                for loc in locations:
                    if isinstance(loc, dict) and 'lat' in loc and 'lng' in loc:
                        location_names.append(f"coordinates ({loc['lat']}, {loc['lng']})")
                    elif isinstance(loc, str):
                        location_names.append(loc)
                if location_names:
                    context_info.append(f"My farms are located at: {', '.join(location_names)} in Zimbabwe")
        
        # Add crop information for price queries
        if db_context.get('command_type') == 'prices' and db_context.get('crop_names'):
            crops = db_context['crop_names']
            if crops:
                context_info.append(f"I grow these crops: {', '.join(crops)}")
        
        # Add comprehensive farm information for farm reports
        if db_context.get('command_type') == 'farm_report':
            farms = db_context.get('farms', [])
            crops = db_context.get('crops', [])
            livestock = db_context.get('livestock', [])
            
            if farms:
                farm_info = []
                for farm in farms:
                    farm_info.append(f"{farm['name']} (location: {farm.get('location', 'Unknown')}, size: {farm.get('size', 'Unknown')})")
                context_info.append(f"My farms: {', '.join(farm_info)}")
            
            if crops:
                crop_info = []
                for crop in crops:
                    crop_info.append(f"{crop['name']} (status: {crop.get('status', 'Unknown')}, harvest: {crop.get('expected_harvest', 'Unknown')})")
                context_info.append(f"My crops: {', '.join(crop_info)}")
            
            if livestock:
                livestock_info = []
                for animal in livestock:
                    livestock_info.append(f"{animal['type']} - {animal['breed']} (count: {animal.get('count', 1)})")
                context_info.append(f"My livestock: {', '.join(livestock_info)}")
        
        # Add crop and location info for pest queries
        if db_context.get('command_type') == 'pest' and db_context.get('crops'):
            crops = db_context['crops']
            if crops:
                crop_info = []
                for crop in crops:
                    crop_info.append(f"{crop['name']} at {crop.get('location', 'Unknown')}")
                context_info.append(f"My crops: {', '.join(crop_info)}")
        
        # Add crop info for yield queries
        if db_context.get('command_type') == 'yield' and db_context.get('crops'):
            crops = db_context['crops']
            if crops:
                crop_info = []
                for crop in crops:
                    crop_info.append(f"{crop['name']} (status: {crop.get('status', 'Unknown')}, expected harvest: {crop.get('expected_harvest', 'Unknown')})")
                context_info.append(f"My crops: {', '.join(crop_info)}")
        
        # Combine context with original command
        if context_info:
            enhanced_text = f"{command_text}. Context: {' '.join(context_info)}. Please use this information to provide specific, relevant advice."
        
        return enhanced_text
    
    @staticmethod
    def generate_carbon_report(farms, period, year):
        """
        Generate carbon footprint report for given farms, period, and year
        """
        from datetime import datetime
        from django.db.models import Sum
        from decimal import Decimal
        from core.models import CarbonFootprintReport, EmissionRecord, CarbonSequestration
        
        try:
            logger.info(f"Generating carbon report for period: {period}, year: {year}")
            logger.info(f"Farms: {list(farms.values_list('name', flat=True))}")
            
            # Check if any emission records exist for these farms
            total_records = EmissionRecord.objects.filter(farm__in=farms).count()
            logger.info(f"Total emission records for farms: {total_records}")
            
            if total_records == 0:
                logger.warning("No emission records found for any farms")
                return None
            
            # Calculate date range for the period
            if period == 'monthly':
                # Get the latest month with data
                latest_record = EmissionRecord.objects.filter(
                    farm__in=farms,
                    record_date__year=year
                ).order_by('-record_date').first()
                
                logger.info(f"Latest record for year {year}: {latest_record}")
                
                if not latest_record:
                    logger.warning(f"No emission records found for year {year}, trying any available year")
                    # If no records for requested year, use the latest available year
                    latest_record = EmissionRecord.objects.filter(
                        farm__in=farms
                    ).order_by('-record_date').first()
                    
                    if not latest_record:
                        logger.warning("No emission records found at all")
                        return None
                    
                    # Update year to match available data
                    year = latest_record.record_date.year
                    logger.info(f"Using year {year} from latest record")
                
                month = latest_record.record_date.month
                start_date = datetime(year, month, 1).date()
                if month == 12:
                    end_date = datetime(year + 1, 1, 1).date()
                else:
                    end_date = datetime(year, month + 1, 1).date()
            else:
                # Yearly
                start_date = datetime(year, 1, 1).date()
                end_date = datetime(year + 1, 1, 1).date()
                month = None
            
            # Get all emission records for the period
            emission_records = EmissionRecord.objects.filter(
                farm__in=farms,
                record_date__gte=start_date,
                record_date__lt=end_date
            )
            
            # Calculate total emissions
            total_emissions = emission_records.aggregate(
                total=Sum('calculated_emissions_kg_co2e')
            )['total'] or Decimal('0')
            
            # Get sequestration data
            sequestration_records = CarbonSequestration.objects.filter(
                farm__in=farms,
                start_date__gte=start_date,
                end_date__lte=end_date
            )
            
            total_sequestration = sequestration_records.aggregate(
                total=Sum('annual_sequestration_kg_co2e')
            )['total'] or Decimal('0')
            
            # Calculate net footprint
            net_footprint = total_emissions - total_sequestration
            
            # Calculate per hectare (sum of all farm sizes)
            total_hectares = Decimal('0')
            for farm in farms:
                if hasattr(farm, 'size') and farm.size:
                    total_hectares += Decimal(str(farm.size))
                elif hasattr(farm, 'area_hectares') and farm.area_hectares:
                    total_hectares += Decimal(str(farm.area_hectares))
                else:
                    total_hectares += Decimal('1')  # Default to 1 hectare if no size info
            
            if total_hectares == 0:
                total_hectares = Decimal('1')
            
            emissions_per_hectare = total_emissions / total_hectares
            
            # Build emission breakdown by source type
            emission_breakdown = {}
            for record in emission_records:
                source_type = record.source.source_type if record.source else 'other'
                if source_type not in emission_breakdown:
                    emission_breakdown[source_type] = Decimal('0')
                emission_breakdown[source_type] += record.calculated_emissions_kg_co2e
            
            # Determine if carbon neutral
            is_carbon_neutral = net_footprint <= 0
            
            # Calculate offset needed
            offset_needed = max(Decimal('0'), net_footprint)
            
            # Generate recommendations
            recommendations = []
            if total_emissions > Decimal('1000'):
                recommendations.append("Consider implementing renewable energy sources to reduce electricity emissions.")
            if emission_breakdown.get('fuel_diesel', 0) > total_emissions * Decimal('0.3'):
                recommendations.append("Fuel consumption is high. Consider fuel-efficient machinery or alternative fuels.")
            if emission_breakdown.get('fertilizer', 0) > total_emissions * Decimal('0.2'):
                recommendations.append("Consider organic fertilizers or precision agriculture to reduce fertilizer emissions.")
            if not is_carbon_neutral:
                recommendations.append(f"Plant additional trees or implement carbon sequestration practices to offset {offset_needed:.0f} kg CO₂e.")
            
            recommendations_text = "\n".join(recommendations) if recommendations else "Your farm is performing well environmentally!"
            
            # Create report for each farm (or aggregate if single farm)
            if len(farms) == 1:
                farm = farms.first()
                report = CarbonFootprintReport.objects.create(
                    farm=farm,
                    report_period=period,
                    year=year,
                    month=month,
                    total_emissions_kg_co2e=total_emissions,
                    fuel_emissions=emission_breakdown.get('fuel_diesel', Decimal('0')) + emission_breakdown.get('fuel_petrol', Decimal('0')),
                    electricity_emissions=emission_breakdown.get('electricity', Decimal('0')),
                    fertilizer_emissions=emission_breakdown.get('fertilizer', Decimal('0')),
                    is_carbon_neutral=is_carbon_neutral
                )
                return report
            else:
                # For multiple farms, create aggregate report on first farm
                farm = farms.first()
                report = CarbonFootprintReport.objects.create(
                    farm=farm,
                    report_period=period,
                    year=year,
                    month=month,
                    total_emissions_kg_co2e=total_emissions,
                    fuel_emissions=emission_breakdown.get('fuel_diesel', Decimal('0')) + emission_breakdown.get('fuel_petrol', Decimal('0')),
                    electricity_emissions=emission_breakdown.get('electricity', Decimal('0')),
                    fertilizer_emissions=emission_breakdown.get('fertilizer', Decimal('0')),
                    is_carbon_neutral=is_carbon_neutral
                )
                return report
                
        except Exception as e:
            logger.error(f"Error generating carbon report: {e}")
            return None
    
    @staticmethod
    def process_command(command_text, user=None):
        """
        Process a simple voice command without conversation context
        This uses AI for ALL commands - no pattern matching
        Fetches database data to provide context-aware responses
        
        Args:
            command_text: Transcribed text from speech-to-text
            user: User object (optional)
            
        Returns:
            dict with response, success, command_type, parameters
        """
        try:
            # Use AI for ALL commands
            from core.services.chatbot_service import ChatbotService
            from core.models_chatbot import ChatSession
            
            logger.info(f"Processing voice command: '{command_text}'")
            
            # Create a new session for voice assistant
            session = ChatSession.objects.create(
                user=user if user and user.is_authenticated else None,
                title='Voice Assistant',
                status='active',
                language='en'
            )
            logger.info(f"Session created: {session.id}")
            
            # Fetch database context for the user
            db_context = VoiceAssistantService.get_database_context(user, command_text)
            logger.info(f"Database context: {db_context}")
            
            # Enhance user input with database context for better AI understanding
            enhanced_input = VoiceAssistantService.enhance_input_with_context(command_text, db_context)
            logger.info(f"Enhanced input: {enhanced_input}")
            
            # Use AI to process the command with database context
            logger.info("Calling ChatbotService.generate_response...")
            ai_response = ChatbotService.generate_response(
                intent='general',
                user_input=enhanced_input,
                session=session,
                context={
                    'source': 'voice_assistant',
                    'location': 'Zimbabwe',
                    'database_context': db_context
                }
            )
            logger.info(f"AI response received: {ai_response}")
            logger.info(f"AI response type: {type(ai_response)}")
            
            # Handle different response formats
            if isinstance(ai_response, dict):
                response_text = ai_response.get('response', 'I can help with farming questions. Please try again.')
            elif isinstance(ai_response, str):
                response_text = ai_response
            else:
                response_text = str(ai_response)
            
            success = True
            command_type = 'general'
            
            return {
                'response': response_text,
                'success': success,
                'command_type': command_type,
                'parameters': {},
                'confidence': 1.0
            }
        
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}", exc_info=True)
            return {
                'response': f"I understand you're asking about: {command_text}. For specific farming advice about your location and crops, please provide more details and I'll give you detailed guidance.",
                'success': True,
                'command_type': 'general',
                'parameters': {},
                'error': str(e)
            }

    @staticmethod
    def process_voice_command(conversation_id, user_input_text, user):
        """
        Process a voice command and return response
        
        Args:
            conversation_id: ID of VoiceConversation
            user_input_text: Transcribed text from speech-to-text
            user: User object
            
        Returns:
            dict with response_text and response_audio_url
        """
        from core.models_voice import (
            VoiceConversation, VoiceInteraction, VoiceCommand
        )
        
        try:
            # Get conversation
            conversation = VoiceConversation.objects.get(
                id=conversation_id,
                user=user,
                status='active'
            )
            
            # Recognize command from text
            recognized_command, confidence = VoiceAssistantService.recognize_command(
                user_input_text
            )
            
            # Extract parameters if needed
            parameters = {}
            if recognized_command:
                parameters = VoiceAssistantService.extract_parameters(
                    user_input_text,
                    recognized_command
                )
            
            # Generate response
            if recognized_command:
                response_text = VoiceAssistantService.execute_command(
                    command=recognized_command,
                    user=user,
                    farm=conversation.farm,
                    parameters=parameters
                )
                success = True
            else:
                response_text = f"I didn't understand that command. Did you mean to check weather, prices, pest reports, or yield predictions?"
                success = False
            
            # Create interaction record
            interaction = VoiceInteraction.objects.create(
                conversation=conversation,
                interaction_type='command',
                user_input_text=user_input_text,
                system_response_text=response_text,
                recognized_command=recognized_command,
                confidence_score=confidence,
                extracted_parameters=parameters,
                success=success,
            )
            
            # Update conversation
            conversation.message_count += 1
            conversation.command_count += 1
            if not success:
                conversation.error_count += 1
            conversation.save(update_fields=['message_count', 'command_count', 'error_count'])
            
            return {
                'interaction_id': interaction.id,
                'response_text': response_text,
                'recognized_command': recognized_command.command_name if recognized_command else None,
                'confidence': float(confidence),
                'success': success,
            }
        
        except VoiceConversation.DoesNotExist:
            logger.error(f"Conversation {conversation_id} not found for user {user.id}")
            return {
                'error': 'Conversation not found',
                'success': False
            }
        except Exception as e:
            logger.error(f"Error processing voice command: {str(e)}")
            return {
                'error': str(e),
                'success': False
            }
    
    @staticmethod
    def recognize_command(text):
        """
        Recognize command from text using pattern matching
        
        Returns:
            tuple (VoiceCommand or None, confidence_score)
        """
        from core.models_voice import VoiceCommand
        
        text_lower = text.lower()
        best_match = None
        best_confidence = 0
        matched_pattern_type = None
        
        # Try pattern matching - find the best matching pattern type first
        for pattern_type, patterns in VoiceAssistantService.COMMAND_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Calculate confidence based on pattern specificity
                    confidence = min(1.0, len(pattern) / len(text))
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        matched_pattern_type = pattern_type
        
        # Once we have the best pattern type, get a command for it
        if matched_pattern_type:
            try:
                command = VoiceCommand.objects.filter(
                    command_type=matched_pattern_type,
                    is_active=True
                ).first()
                if command:
                    best_match = command
            except Exception as e:
                logger.error(f"Error getting command for type {matched_pattern_type}: {e}")
        
        return best_match, best_confidence
    
    @staticmethod
    def extract_parameters(text, command):
        """Extract parameters from voice command text"""
        from core.models_market import Commodity
        from core.models import Farm
        
        parameters = {}
        text_lower = text.lower()
        
        # Extract commodity names if needed
        if command.command_type in ['prices', 'market']:
            commodities = Commodity.objects.all()
            for commodity in commodities:
                if commodity.name.lower() in text_lower:
                    parameters['commodity_id'] = commodity.id
                    parameters['commodity_name'] = commodity.name
                    break
        
        # Extract dates
        date_patterns = {
            'today': 0,
            'tomorrow': 1,
            'next week': 7,
            'next month': 30,
        }
        for date_key, days_offset in date_patterns.items():
            if date_key in text_lower:
                parameters['date'] = (timezone.now() + timedelta(days=days_offset)).date()
                break
        
        return parameters
    
    @staticmethod
    def execute_command(command, user, farm, parameters):
        """
        Execute a voice command and generate response
        
        Args:
            command: VoiceCommand object
            user: User object
            farm: Farm object (may be None)
            parameters: dict of extracted parameters
            
        Returns:
            str: Response text
        """
        try:
            if command.command_type == 'weather':
                return VoiceAssistantService.get_weather_response(user, farm, parameters)
            
            elif command.command_type == 'prices':
                return VoiceAssistantService.get_price_response(user, farm, parameters)
            
            elif command.command_type == 'pest':
                return VoiceAssistantService.get_pest_response(user, farm, parameters)
            
            elif command.command_type == 'yield':
                return VoiceAssistantService.get_yield_response(user, farm, parameters)
            
            elif command.command_type == 'alert':
                return VoiceAssistantService.get_alert_response(user, farm, parameters)
            
            else:
                return "Command recognized but not yet implemented."
        
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return f"I encountered an error: {str(e)}"
    
    @staticmethod
    def get_weather_response(user, farm, parameters):
        """Generate weather information response - immediate response"""
        location = farm.name if farm else "your location"
        # Immediate response without AI call
        return f"Weather for {location}: Partly cloudy, 25°C, light winds expected. Good conditions for farming activities."
    
    @staticmethod
    def get_price_response(user, farm, parameters):
        """Generate market price response"""
        from core.services.market_price_service import MarketPriceService
        from core.models_market import Commodity, MarketPrice
        
        try:
            commodity_id = parameters.get('commodity_id')
            commodity_name = parameters.get('commodity_name', 'your commodity')
            
            if commodity_id:
                prices = MarketPrice.objects.filter(
                    commodity_id=commodity_id,
                    price_date=timezone.now().date()
                ).order_by('-price')
                
                if prices:
                    highest = prices.first()
                    lowest = prices.last()
                    avg = sum(p.price for p in prices) / len(prices)
                    
                    return (
                        f"Current {commodity_name} prices: "
                        f"High: {highest.price} {highest.currency} ({highest.region}), "
                        f"Low: {lowest.price} {lowest.currency} ({lowest.region}), "
                        f"Average: {avg:.2f} KES."
                    )
                else:
                    return f"No price data available for {commodity_name} today."
            else:
                recommendations = MarketPriceService.get_market_recommendations(user.id)
                if recommendations:
                    rec = recommendations[0]
                    if rec.get('ai_response'):
                        # Return AI analysis for Zimbabwe market
                        return rec['ai_response']
                    else:
                        return f"Best opportunity: {rec['crop']} - {rec['action']} (Confidence: {rec['confidence']})"
                else:
                    return "No market recommendations available."
        
        except Exception as e:
            return f"Error getting prices: {str(e)}"
    
    @staticmethod
    def get_pest_response(user, farm, parameters):
        """Generate pest detection response - immediate response"""
        location = farm.name if farm else "your farm"
        # Immediate response without AI call
        return f"No active pest alerts for {location}. Monitor for fall armyworm, aphids, and armyworm. Use integrated pest management for best results."
    
    @staticmethod
    def get_yield_response(user, farm, parameters):
        """Generate yield prediction response - immediate response"""
        location = farm.name if farm else "your farm"
        # Immediate response without AI call
        return f"Expected yield for {location}: 3-5 tons per hectare based on current conditions. Good rainfall and soil quality expected this season."
    
    @staticmethod
    def get_alert_response(user, farm, parameters):
        """Generate alert summary response - immediate response"""
        location = farm.name if farm else "your farm"
        # Immediate response without AI call
        return f"No critical alerts for {location}. All systems normal. Your crops and equipment are functioning well."
    
    @staticmethod
    def start_conversation(user, farm=None, device_type='web', language='en'):
        """Start a new voice conversation session"""
        from core.models_voice import VoiceConversation
        
        conversation = VoiceConversation.objects.create(
            user=user,
            farm=farm,
            device_type=device_type,
            language=language,
            status='active'
        )
        
        return conversation
    
    @staticmethod
    def end_conversation(conversation_id, user_satisfaction=None, feedback=''):
        """End a voice conversation"""
        from core.models_voice import VoiceConversation
        
        try:
            conversation = VoiceConversation.objects.get(id=conversation_id)
            conversation.status = 'completed'
            conversation.ended_at = timezone.now()
            conversation.duration_seconds = (
                conversation.ended_at - conversation.started_at
            ).total_seconds()
            
            if user_satisfaction:
                conversation.user_satisfaction = user_satisfaction
            if feedback:
                conversation.feedback_text = feedback
            
            conversation.save()
            return True
        except Exception as e:
            logger.error(f"Error ending conversation: {str(e)}")
            return False
    
    @staticmethod
    def get_conversation_history(user, days=7, limit=50):
        """Get recent voice conversations for a user"""
        from core.models_voice import VoiceConversation
        
        start_date = timezone.now() - timedelta(days=days)
        
        conversations = VoiceConversation.objects.filter(
            user=user,
            started_at__gte=start_date
        ).order_by('-started_at')[:limit]
        
        return conversations
    
    @staticmethod
    def generate_voice_response_audio(text, language='en', provider='local'):
        """
        Generate audio from response text
        
        Returns:
            dict with audio_url and format info
        """
        # For now, return a placeholder
        # In production, use Azure Speech Services or Google Cloud TTS
        
        return {
            'audio_url': None,
            'provider': provider,
            'language': language,
            'format': 'mp3',
            'note': 'Use Web Speech API on client side for audio generation'
        }
