#!/usr/bin/env python
"""
Setup script to populate VoiceCommand table with sample commands
Run with: python setup_voice_commands.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models_voice import VoiceCommand

# Sample voice commands for agriculture
commands_data = [
    {
        'command_name': 'Check Weather',
        'command_type': 'weather',
        'description': 'Get current weather forecast for your farm',
        'voice_variants': ['what is the weather', 'weather forecast', 'how is the weather', 'check the weather'],
        'handler_function': 'handle_weather_check',
        'requires_farm_context': True,
        'requires_parameters': {'farm_id': 'int'},
    },
    {
        'command_name': 'Check Rain Forecast',
        'command_type': 'weather',
        'description': 'Get rain prediction for the next few days',
        'voice_variants': ['will it rain', 'rain forecast', 'when will it rain', 'chance of rain'],
        'handler_function': 'handle_rain_forecast',
        'requires_farm_context': True,
        'requires_parameters': {'farm_id': 'int'},
    },
    {
        'command_name': 'Check Crop Prices',
        'command_type': 'prices',
        'description': 'Get current market prices for crops',
        'voice_variants': ['crop prices', 'market prices', 'how much for crops', 'price of maize'],
        'handler_function': 'handle_crop_prices',
        'requires_farm_context': False,
        'requires_parameters': {'crop': 'str'},
    },
    {
        'command_name': 'Check Livestock Prices',
        'command_type': 'prices',
        'description': 'Get current market prices for livestock',
        'voice_variants': ['livestock prices', 'cattle prices', 'goat prices', 'animal prices'],
        'handler_function': 'handle_livestock_prices',
        'requires_farm_context': False,
        'requires_parameters': {'animal_type': 'str'},
    },
    {
        'command_name': 'Report Pest',
        'command_type': 'pest',
        'description': 'Report a pest sighting on your farm',
        'voice_variants': ['report pest', 'i see pests', 'pest problem', 'found bugs'],
        'handler_function': 'handle_pest_report',
        'requires_farm_context': True,
        'requires_parameters': {'farm_id': 'int', 'pest_type': 'str'},
    },
    {
        'command_name': 'Get Pest Advice',
        'command_type': 'pest',
        'description': 'Get advice on treating pest problems',
        'voice_variants': ['pest advice', 'how to treat pests', 'pest control', 'get rid of pests'],
        'handler_function': 'handle_pest_advice',
        'requires_farm_context': False,
        'requires_parameters': {'pest_type': 'str'},
    },
    {
        'command_name': 'Predict Yield',
        'command_type': 'yield',
        'description': 'Get yield prediction for your crops',
        'voice_variants': ['yield prediction', 'estimate yield', 'how much will i harvest', 'crop yield'],
        'handler_function': 'handle_yield_prediction',
        'requires_farm_context': True,
        'requires_parameters': {'farm_id': 'int', 'crop_id': 'int'},
    },
    {
        'command_name': 'Add Farm Task',
        'command_type': 'task',
        'description': 'Add a new task to your farm schedule',
        'voice_variants': ['add task', 'new task', 'schedule task', 'remind me to'],
        'handler_function': 'handle_add_task',
        'requires_farm_context': True,
        'requires_parameters': {'farm_id': 'int', 'task_name': 'str', 'due_date': 'date'},
    },
    {
        'command_name': 'List Tasks',
        'command_type': 'task',
        'description': 'List all pending farm tasks',
        'voice_variants': ['show tasks', 'my tasks', 'pending tasks', 'what do i need to do'],
        'handler_function': 'handle_list_tasks',
        'requires_farm_context': True,
        'requires_parameters': {'farm_id': 'int'},
    },
    {
        'command_name': 'Set Reminder',
        'command_type': 'reminder',
        'description': 'Set a reminder for farm activities',
        'voice_variants': ['set reminder', 'remind me', 'add reminder', 'don\'t forget to'],
        'handler_function': 'handle_set_reminder',
        'requires_farm_context': False,
        'requires_parameters': {'reminder_text': 'str', 'reminder_time': 'datetime'},
    },
    {
        'command_name': 'Check Alerts',
        'command_type': 'alert',
        'description': 'Check for important farm alerts',
        'voice_variants': ['check alerts', 'any alerts', 'show alerts', 'important notifications'],
        'handler_function': 'handle_check_alerts',
        'requires_farm_context': True,
        'requires_parameters': {'farm_id': 'int'},
    },
    {
        'command_name': 'Get Farming Advice',
        'command_type': 'advice',
        'description': 'Get general farming advice and tips',
        'voice_variants': ['farming advice', 'agriculture tips', 'farming tips', 'help with farming'],
        'handler_function': 'handle_farming_advice',
        'requires_farm_context': False,
        'requires_parameters': {'topic': 'str'},
    },
    {
        'command_name': 'Check Irrigation',
        'command_type': 'task',
        'description': 'Check irrigation status and schedule',
        'voice_variants': ['irrigation status', 'check irrigation', 'water schedule', 'irrigation needs'],
        'handler_function': 'handle_irrigation_check',
        'requires_farm_context': True,
        'requires_parameters': {'farm_id': 'int'},
    },
    {
        'command_name': 'Check Soil Health',
        'command_type': 'advice',
        'description': 'Get soil health recommendations',
        'voice_variants': ['soil health', 'check soil', 'soil condition', 'soil advice'],
        'handler_function': 'handle_soil_health',
        'requires_farm_context': True,
        'requires_parameters': {'farm_id': 'int'},
    },
    {
        'command_name': 'Market Analysis',
        'command_type': 'prices',
        'description': 'Get market analysis and trends',
        'voice_variants': ['market analysis', 'market trends', 'price trends', 'market outlook'],
        'handler_function': 'handle_market_analysis',
        'requires_farm_context': False,
        'requires_parameters': {'commodity': 'str'},
    },
]

def setup_voice_commands():
    """Populate VoiceCommand table with sample data"""
    print("Setting up voice commands...")
    
    created_count = 0
    updated_count = 0
    
    for cmd_data in commands_data:
        command, created = VoiceCommand.objects.get_or_create(
            command_name=cmd_data['command_name'],
            command_type=cmd_data['command_type'],
            defaults=cmd_data
        )
        
        if created:
            created_count += 1
            print(f"✓ Created: {command.command_name}")
        else:
            # Update existing command
            for key, value in cmd_data.items():
                setattr(command, key, value)
            command.save()
            updated_count += 1
            print(f"✓ Updated: {command.command_name}")
    
    print(f"\n✅ Setup complete!")
    print(f"   Created: {created_count} commands")
    print(f"   Updated: {updated_count} commands")
    print(f"   Total: {VoiceCommand.objects.count()} commands")

if __name__ == '__main__':
    setup_voice_commands()
