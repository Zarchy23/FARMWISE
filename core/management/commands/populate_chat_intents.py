# core/management/commands/populate_chat_intents.py
# Management command to populate initial chat intents

from django.core.management.base import BaseCommand
from core.models_chatbot import ChatIntent


class Command(BaseCommand):
    help = 'Populate initial chat intents for FarmWise chatbot'
    
    def handle(self, *args, **options):
        intents = [
            # Crop Advice Intents
            {
                'intent_name': 'Planting Season',
                'category': 'crop_advice',
                'keywords': ['when plant', 'planting season', 'best time plant', 'plant maize', 'plant wheat', 'sow seeds'],
                'description': 'Information about the best planting times for different crops',
                'response_template': 'The planting season depends on your crop and local climate. For most crops, prepare the soil 2-3 weeks before planting.',
            },
            {
                'intent_name': 'Crop Selection',
                'category': 'crop_advice',
                'keywords': ['what crop', 'which crop', 'crop recommendations', 'best crop', 'profitable crop'],
                'description': 'Recommendations for crop selection based on climate and soil',
                'response_template': 'Crop selection depends on your soil type, climate, water availability, and market demand.',
            },
            {
                'intent_name': 'Crop Rotation',
                'category': 'crop_advice',
                'keywords': ['crop rotation', 'rotate crops', 'succession planting', 'next season'],
                'description': 'Advice on crop rotation practices',
                'response_template': 'Crop rotation helps maintain soil fertility. Rotate legumes with cereals to improve nitrogen.',
            },
            
            # Pest & Disease Intents
            {
                'intent_name': 'Pest Detection',
                'category': 'pest_disease',
                'keywords': ['pests', 'insects', 'bugs', 'pest report', 'detect pest', 'pest problem'],
                'description': 'Help identifying and detecting pests',
                'response_template': 'Describe the pest characteristics: color, size, where found, and symptoms on plants.',
            },
            {
                'intent_name': 'Disease Diagnosis',
                'category': 'pest_disease',
                'keywords': ['disease', 'disease detection', 'leaf spots', 'wilting', 'yellowing', 'rot'],
                'description': 'Help diagnosing crop diseases',
                'response_template': 'Crop diseases can show as spots, wilting, or discoloration. Please describe the symptoms in detail.',
            },
            {
                'intent_name': 'Pest Control',
                'category': 'pest_disease',
                'keywords': ['control pests', 'pest treatment', 'pesticide', 'organic pest control', 'pest management'],
                'description': 'Pest and disease management strategies',
                'response_template': 'Integrated pest management includes cultural practices, biological controls, and chemical options.',
            },
            
            # Weather & Climate Intents
            {
                'intent_name': 'Weather Forecast',
                'category': 'weather',
                'keywords': ['weather', 'forecast', 'rain', 'temperature', 'wind', 'climate'],
                'description': 'Current weather and forecast information',
                'response_template': 'Check the weather dashboard for your location\'s forecast and plan farming activities accordingly.',
            },
            {
                'intent_name': 'Climate Impact',
                'category': 'weather',
                'keywords': ['drought', 'flood', 'climate', 'cold', 'heat', 'extreme weather'],
                'description': 'Impact of climate conditions on crops',
                'response_template': 'Climate challenges require specific management strategies. Implement irrigation or drainage as needed.',
            },
            
            # Market & Prices Intents
            {
                'intent_name': 'Market Prices',
                'category': 'market',
                'keywords': ['market prices', 'commodity price', 'crop price', 'sell price', 'buy price', 'market rate'],
                'description': 'Current market prices for commodities',
                'response_template': 'Check the Market Prices section to see real-time commodity prices in your region.',
            },
            {
                'intent_name': 'Price Trends',
                'category': 'market',
                'keywords': ['price trend', 'trend analysis', 'price forecast', 'selling time', 'best time sell'],
                'description': 'Price trend analysis and selling recommendations',
                'response_template': 'Price trends help identify the best selling time. Check the price trends dashboard for your crops.',
            },
            {
                'intent_name': 'Direct Sales',
                'category': 'market',
                'keywords': ['sell crop', 'direct sale', 'listing', 'marketplace', 'buyer', 'sell online'],
                'description': 'Information about selling directly through marketplace',
                'response_template': 'You can create direct sales listings in the Marketplace section to connect with buyers.',
            },
            
            # Soil & Fertilizer Intents
            {
                'intent_name': 'Soil Testing',
                'category': 'soil',
                'keywords': ['soil test', 'soil analysis', 'soil type', 'soil pH', 'soil fertility', 'soil quality'],
                'description': 'Soil testing and analysis information',
                'response_template': 'Regular soil testing helps understand nutrient levels and pH. Use results to guide fertilizer application.',
            },
            {
                'intent_name': 'Fertilizer Application',
                'category': 'soil',
                'keywords': ['fertilizer', 'nutrients', 'nitrogen', 'phosphorus', 'potassium', 'NPK', 'compost', 'manure'],
                'description': 'Guidance on fertilizer use and application',
                'response_template': 'Apply fertilizers based on soil test results and crop nutrient requirements.',
            },
            {
                'intent_name': 'Soil Improvement',
                'category': 'soil',
                'keywords': ['improve soil', 'soil enhancement', 'soil amendment', 'organic matter', 'mulch'],
                'description': 'Methods to improve soil health and fertility',
                'response_template': 'Improve soil with organic matter, cover crops, and reduced tillage practices.',
            },
            
            # Irrigation Intents
            {
                'intent_name': 'Irrigation Scheduling',
                'category': 'irrigation',
                'keywords': ['irrigation', 'watering', 'water schedule', 'how much water', 'when water', 'irrigation schedule'],
                'description': 'When and how much to irrigate',
                'response_template': 'Irrigation depends on rainfall, soil type, and crop stage. Water deeply but less frequently.',
            },
            {
                'intent_name': 'Irrigation Methods',
                'category': 'irrigation',
                'keywords': ['drip irrigation', 'sprinkler', 'flood irrigation', 'furrow', 'irrigation method', 'water efficiency'],
                'description': 'Different irrigation methods and efficiency',
                'response_template': 'Drip and sprinkler irrigation are water-efficient. Choose based on crop and soil type.',
            },
            
            # Harvesting Intents
            {
                'intent_name': 'Harvest Timing',
                'category': 'harvesting',
                'keywords': ['harvest', 'harvesting time', 'ready harvest', 'crop maturity', 'mature', 'ripe'],
                'description': 'When to harvest crops',
                'response_template': 'Harvest at the right stage for best quality. Check crop indicators: color, moisture, size.',
            },
            {
                'intent_name': 'Harvest Methods',
                'category': 'harvesting',
                'keywords': ['harvesting method', 'harvest technique', 'collect', 'pick', 'cut', 'mechanical harvest'],
                'description': 'Harvesting techniques and best practices',
                'response_template': 'Choose harvesting methods that minimize crop damage and loss.',
            },
            
            # Storage & Preservation
            {
                'intent_name': 'Storage Conditions',
                'category': 'storage',
                'keywords': ['storage', 'store crop', 'storage condition', 'temperature', 'humidity', 'preservation'],
                'description': 'Proper crop storage and preservation',
                'response_template': 'Store crops in cool, dry conditions. Maintain proper temperature and humidity for each crop.',
            },
            
            # Financial Planning
            {
                'intent_name': 'Profitability Analysis',
                'category': 'financial',
                'keywords': ['profit', 'cost', 'revenue', 'income', 'financial', 'return', 'investment'],
                'description': 'Farm profitability and financial planning',
                'response_template': 'Track costs and revenue to analyze profitability. Plan for best ROI on investments.',
            },
            
            # General Questions
            {
                'intent_name': 'General Farming Advice',
                'category': 'general',
                'keywords': ['advice', 'help', 'question', 'farming', 'what', 'how', 'why', 'when'],
                'description': 'General agricultural advice',
                'response_template': 'I\'m here to help with farming questions. Could you be more specific about your concern?',
            },
        ]
        
        created_count = 0
        for intent_data in intents:
            intent, created = ChatIntent.objects.get_or_create(
                intent_name=intent_data['intent_name'],
                defaults={
                    'category': intent_data['category'],
                    'keywords': intent_data['keywords'],
                    'description': intent_data['description'],
                    'response_template': intent_data['response_template'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {intent.intent_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {intent.intent_name}'))
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully created {created_count} chat intents!')
        )
