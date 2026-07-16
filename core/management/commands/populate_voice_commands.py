# core/management/commands/populate_voice_commands.py
# Management command to populate initial voice commands

from django.core.management.base import BaseCommand
from core.models_voice import VoiceCommand

class Command(BaseCommand):
    help = 'Populate initial voice commands for FarmWise voice assistant'
    
    def handle(self, *args, **options):
        commands = [
            # Weather commands
            {
                'command_name': 'Check Weather',
                'command_type': 'weather',
                'description': 'Get current and forecast weather information',
                'voice_variants': [
                    'what is the weather',
                    'weather forecast',
                    'tell me the weather',
                    'how is the weather',
                    'weather today',
                ],
                'handler_function': 'get_weather_response',
                'requires_farm_context': True,
            },
            # Price commands
            {
                'command_name': 'Check Prices',
                'command_type': 'prices',
                'description': 'Get current commodity market prices',
                'voice_variants': [
                    'what is the price of maize',
                    'market prices',
                    'commodity prices',
                    'how much is my crop worth',
                    'check prices',
                ],
                'handler_function': 'get_price_response',
                'requires_farm_context': False,
                'requires_parameters': {'commodity': 'string'},
            },
            # Pest commands
            {
                'command_name': 'Pest Report',
                'command_type': 'pest',
                'description': 'Report and detect pests and diseases',
                'voice_variants': [
                    'report pest',
                    'detect disease',
                    'pest detection',
                    'I have pests',
                    'check for pests',
                ],
                'handler_function': 'get_pest_response',
                'requires_farm_context': True,
            },
            # Yield commands
            {
                'command_name': 'Predict Yield',
                'command_type': 'yield',
                'description': 'Get yield prediction for crops',
                'voice_variants': [
                    'predict yield',
                    'how much will I harvest',
                    'yield prediction',
                    'expected harvest',
                    'crop yield forecast',
                ],
                'handler_function': 'get_yield_response',
                'requires_farm_context': True,
            },
            # Reminder commands
            {
                'command_name': 'Set Reminder',
                'command_type': 'reminder',
                'description': 'Create reminders and alarms',
                'voice_variants': [
                    'remind me',
                    'set alarm',
                    'create reminder',
                    'remind me tomorrow',
                    'set a reminder',
                ],
                'handler_function': 'set_reminder',
                'requires_farm_context': False,
                'requires_parameters': {'reminder_text': 'string', 'when': 'datetime'},
            },
            # Alert commands
            {
                'command_name': 'Check Alerts',
                'command_type': 'alert',
                'description': 'Check alerts and notifications',
                'voice_variants': [
                    'any alerts',
                    'what is new',
                    'notifications',
                    'check alerts',
                    'alert status',
                ],
                'handler_function': 'get_alert_response',
                'requires_farm_context': False,
            },
            # Advice commands
            {
                'command_name': 'Farming Advice',
                'command_type': 'advice',
                'description': 'Get agricultural advice and recommendations',
                'voice_variants': [
                    'give me advice',
                    'farming recommendations',
                    'what should I do',
                    'best practices',
                    'farming tips',
                ],
                'handler_function': 'get_farming_advice',
                'requires_farm_context': True,
            },
        ]
        
        created_count = 0
        for command_data in commands:
            command, created = VoiceCommand.objects.get_or_create(
                command_name=command_data['command_name'],
                defaults={
                    'command_type': command_data['command_type'],
                    'description': command_data['description'],
                    'voice_variants': command_data['voice_variants'],
                    'handler_function': command_data['handler_function'],
                    'requires_farm_context': command_data['requires_farm_context'],
                    'requires_parameters': command_data.get('requires_parameters', {}),
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {command.command_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {command.command_name}'))
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully created {created_count} voice commands!')
        )
