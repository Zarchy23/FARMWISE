# core/services/chatbot_service.py
# AI Chatbot Service with NLU and Response Generation

import logging
import re
from django.utils import timezone
from django.db.models import Q
import json

from core.models_chatbot import (
    ChatSession, ChatMessage, ChatIntent, ChatResponse, ChatFeedback, ChatStatistics
)
from core.services.multi_ai_service import MultiAIService

logger = logging.getLogger(__name__)


class ChatbotService:
    """Service for handling chatbot conversations with NLU"""
    
    @staticmethod
    def start_session(user, farm=None, language='en'):
        """Start a new chat session"""
        try:
            session = ChatSession.objects.create(
                user=user,
                farm=farm,
                language=language,
                status='active'
            )
            logger.info(f"Started chat session {session.id} for user {user.username}")
            return session
        except Exception as e:
            logger.error(f"Error starting chat session: {str(e)}")
            raise
    
    @staticmethod
    def end_session(session_id, user_satisfaction=None, feedback=''):
        """End a chat session"""
        try:
            session = ChatSession.objects.get(id=session_id)
            session.status = 'closed'
            session.ended_at = timezone.now()
            session.user_satisfaction = user_satisfaction
            session.feedback = feedback
            session.save()
            logger.info(f"Ended chat session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error ending chat session: {str(e)}")
            return False
    
    @staticmethod
    def recognize_intent(user_input, confidence_threshold=0.7):
        """Recognize user intent from input text using keyword matching"""
        try:
            user_input_lower = user_input.lower()
            matched_intents = []
            
            # Get all active intents
            intents = ChatIntent.objects.filter(is_active=True)
            
            for intent in intents:
                keyword_matches = 0
                total_keywords = len(intent.keywords) if intent.keywords else 0
                
                # Check keyword matches
                if intent.keywords:
                    for keyword in intent.keywords:
                        if keyword.lower() in user_input_lower:
                            keyword_matches += 1
                
                # Calculate confidence score
                if total_keywords > 0:
                    confidence = keyword_matches / total_keywords
                else:
                    confidence = 0.0
                
                if confidence >= confidence_threshold:
                    matched_intents.append({
                        'intent': intent,
                        'confidence': confidence
                    })
            
            # Return best match
            if matched_intents:
                best_match = max(matched_intents, key=lambda x: x['confidence'])
                return best_match['intent'], best_match['confidence']
            
            return None, 0.0
        
        except Exception as e:
            logger.error(f"Error recognizing intent: {str(e)}")
            return None, 0.0
    
    @staticmethod
    def extract_context(user_input, session):
        """Extract contextual information from user input with comprehensive farming keywords"""
        context = {}
        user_input_lower = user_input.lower()
        
        # Extract crop type (comprehensive list)
        crop_keywords = {
            # Cereals
            'maize': 'maize', 'corn': 'maize', 'wheat': 'wheat', 'rice': 'rice',
            'barley': 'barley', 'oats': 'oats', 'sorghum': 'sorghum', 'millet': 'millet',
            'rye': 'rye', 'triticale': 'triticale',
            # Legumes
            'beans': 'beans', 'soybeans': 'soybeans', 'groundnut': 'groundnut', 'peanut': 'groundnut',
            'lentil': 'lentil', 'chickpea': 'chickpea', 'pea': 'pea', 'cowpea': 'cowpea',
            'pigeon pea': 'pigeon pea', 'mung bean': 'mung bean',
            # Vegetables
            'tomato': 'tomato', 'potato': 'potato', 'onion': 'onion', 'garlic': 'garlic',
            'cabbage': 'cabbage', 'lettuce': 'lettuce', 'spinach': 'spinach', 'kale': 'kale',
            'broccoli': 'broccoli', 'cauliflower': 'cauliflower', 'carrot': 'carrot',
            'beetroot': 'beetroot', 'radish': 'radish', 'turnip': 'turnip',
            'pepper': 'pepper', 'chili': 'chili', 'eggplant': 'eggplant', 'okra': 'okra',
            'cucumber': 'cucumber', 'pumpkin': 'pumpkin', 'squash': 'squash',
            'zucchini': 'zucchini', 'melon': 'melon', 'watermelon': 'watermelon',
            # Fruits
            'banana': 'banana', 'mango': 'mango', 'avocado': 'avocado', 'citrus': 'citrus',
            'orange': 'citrus', 'lemon': 'citrus', 'lime': 'citrus', 'grapefruit': 'citrus',
            'apple': 'apple', 'pear': 'pear', 'peach': 'peach', 'plum': 'plum',
            'strawberry': 'strawberry', 'blueberry': 'blueberry', 'raspberry': 'raspberry',
            'pineapple': 'pineapple', 'papaya': 'papaya', 'guava': 'guava',
            # Cash crops
            'coffee': 'coffee', 'tea': 'tea', 'sugarcane': 'sugarcane', 'cotton': 'cotton',
            'tobacco': 'tobacco', 'cocoa': 'cocoa', 'rubber': 'rubber',
            # Oil crops
            'sunflower': 'sunflower', 'sesame': 'sesame', 'mustard': 'mustard',
            'castor': 'castor', 'linseed': 'linseed',
            # Root crops
            'cassava': 'cassava', 'yam': 'yam', 'sweet potato': 'sweet potato', 'taro': 'taro',
            # Others
            'sugarcane': 'sugarcane', 'jute': 'jute', 'hemp': 'hemp'
        }
        for keyword, crop_type in crop_keywords.items():
            if keyword in user_input_lower:
                context['crop'] = crop_type
                break
        
        # Extract livestock type (comprehensive list)
        livestock_keywords = {
            'cattle': 'cattle', 'cow': 'cattle', 'bull': 'cattle', 'calf': 'cattle',
            'sheep': 'sheep', 'lamb': 'sheep', 'ewe': 'sheep', 'ram': 'sheep',
            'goat': 'goat', 'kid': 'goat', 'doe': 'goat', 'buck': 'goat',
            'pig': 'pig', 'hog': 'pig', 'sow': 'pig', 'boar': 'pig',
            'chicken': 'chicken', 'hen': 'chicken', 'rooster': 'chicken', 'chick': 'chicken',
            'duck': 'duck', 'drake': 'duck', 'turkey': 'turkey', 'goose': 'goose',
            'fish': 'fish', 'tilapia': 'fish', 'catfish': 'fish', 'salmon': 'fish',
            'bee': 'bee', 'honeybee': 'bee', 'horse': 'horse', 'donkey': 'donkey',
            'camel': 'camel', 'llama': 'llama', 'alpaca': 'alpaca', 'rabbit': 'rabbit',
            'guinea fowl': 'guinea fowl', 'quail': 'quail', 'pigeon': 'pigeon'
        }
        for keyword, livestock_type in livestock_keywords.items():
            if keyword in user_input_lower:
                context['livestock'] = livestock_type
                break
        
        # Extract comprehensive topic categories
        topic_keywords = {
            'soil_health': ['soil', 'nutrient', 'fertilizer', 'nitrogen', 'phosphorus', 'potassium', 
                          'ph', 'acidity', 'alkalinity', 'organic matter', 'compost', 'manure',
                          'soil testing', 'soil structure', 'texture', 'sand', 'clay', 'loam',
                          'erosion', 'conservation', 'mulch', 'cover crop'],
            'pest_disease': ['pest', 'insect', 'bug', 'disease', 'fungal', 'bacterial', 'virus',
                           'infection', 'infestation', 'outbreak', 'aphid', 'armyworm', 'cutworm',
                           'termite', 'weevil', 'locust', 'thrip', 'whitefly', 'mite',
                           'rust', 'blight', 'mildew', 'rot', 'wilt', 'mosaic', 'spot',
                           'pesticide', 'insecticide', 'fungicide', 'herbicide'],
            'water_management': ['water', 'rain', 'irrigation', 'drought', 'flood', 'drainage',
                               'waterlogging', 'moisture', 'sprinkler', 'drip', 'furrow',
                               'well', 'borehole', 'rainwater', 'harvesting', 'conservation'],
            'market_price': ['price', 'market', 'sell', 'buy', 'cost', 'profit', 'revenue',
                           'income', 'value', 'trading', 'export', 'import', 'demand',
                           'supply', 'trend', 'commodity', 'wholesale', 'retail'],
            'harvesting': ['harvest', 'ripe', 'ready', 'pick', 'gather', 'reaping', 'threshing',
                         'post-harvest', 'storage', 'preservation', 'drying', 'curing'],
            'planting': ['plant', 'seed', 'sow', 'planting', 'germination', 'seedling',
                       'transplant', 'spacing', 'depth', 'seedbed', 'nursery'],
            'weather': ['weather', 'season', 'climate', 'temperature', 'rainfall', 'humidity',
                       'wind', 'frost', 'heat', 'cold', 'dry', 'wet', 'monsoon', 'forecast'],
            'livestock_management': ['feed', 'feeding', 'nutrition', 'grazing', 'pasture',
                                  'breeding', 'mating', 'pregnancy', 'lactation', 'milking',
                                  'vaccination', 'deworming', 'housing', 'shelter'],
            'equipment': ['tractor', 'plow', 'harrow', 'cultivator', 'planter', 'harvester',
                        'sprayer', 'irrigation', 'machine', 'tool', 'equipment', 'machinery',
                        'maintenance', 'repair'],
            'organic_farming': ['organic', 'natural', 'chemical-free', 'pesticide-free',
                             'certified organic', 'biological', 'sustainable', 'eco-friendly'],
            'technology': ['technology', 'digital', 'app', 'software', 'sensor', 'drone',
                         'gps', 'precision', 'automation', 'smart farming', 'iot'],
            'finance': ['loan', 'credit', 'grant', 'subsidy', 'insurance', 'budget', 'cost',
                      'investment', 'capital', 'funding', 'savings', 'bank'],
            'regulations': ['regulation', 'law', 'policy', 'certification', 'standard',
                          'compliance', 'permit', 'license', 'requirement']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                context['topic'] = topic
                break
        
        # Extract region/location indicators
        location_indicators = ['region', 'area', 'zone', 'country', 'province', 'district',
                             'county', 'state', 'location', 'where', 'place', 'near']
        if any(indicator in user_input_lower for indicator in location_indicators):
            context['has_location_query'] = True
        
        # Extract timeframe
        time_keywords = {
            'today': 0, 'tomorrow': 1, 'yesterday': -1,
            'week': 7, 'weekly': 7, 'this week': 7,
            'month': 30, 'monthly': 30, 'this month': 30,
            'season': 90, 'seasonal': 90,
            'year': 365, 'yearly': 365, 'annual': 365, 'this year': 365
        }
        for time_key, days in time_keywords.items():
            if time_key in user_input_lower:
                context['timeframe'] = time_key
                context['timeframe_days'] = days
                break
        
        # Extract problem indicators
        problem_indicators = ['problem', 'issue', 'trouble', 'difficulty', 'challenge',
                           'failing', 'dying', 'dead', 'yellow', 'wilting', 'stunted',
                           'not growing', 'losing', 'attack', 'infected', 'sick']
        if any(indicator in user_input_lower for indicator in problem_indicators):
            context['is_problem'] = True
        
        # Extract urgency indicators
        urgency_indicators = ['urgent', 'emergency', 'immediately', 'asap', 'quickly',
                            'critical', 'serious', 'severe', 'bad']
        if any(indicator in user_input_lower for indicator in urgency_indicators):
            context['is_urgent'] = True
        
        return context
    
    @staticmethod
    def generate_response(intent, user_input, session, context=None):
        """Generate chatbot response using AI with farming expertise"""
        try:
            if context is None:
                context = {}
            
            # Build comprehensive system prompt with agricultural expertise
            system_prompt = """You are FarmWise, an expert agricultural AI assistant with comprehensive knowledge across all aspects of farming and agriculture. You provide accurate, practical, science-based advice to help farmers, agricultural students, researchers, and anyone interested in farming.

## Your Expertise Covers:

### Crop Production & Management
- **Planting**: Seed selection, planting depth, spacing, timing, seed treatment, germination
- **Growing**: Crop nutrition, growth stages, pruning, training, crop rotation, intercropping
- **Harvesting**: Harvest timing, methods, post-harvest handling, storage, preservation
- **Specific Crops**: Cereals (maize, wheat, rice, sorghum, millet), legumes (beans, soybeans, groundnuts), vegetables (tomatoes, potatoes, onions, cabbage, kale), fruits (bananas, mangoes, citrus, avocados), cash crops (coffee, tea, sugarcane, cotton)

### Livestock & Animal Husbandry
- **Cattle**: Breeding, feeding, health management, milk production, beef production
- **Small Ruminants**: Sheep and goat management, breeding, health, meat/milk production
- **Poultry**: Chicken (layers/broilers), ducks, turkeys - housing, feeding, disease prevention
- **Other Animals**: Pigs, fish farming, beekeeping, horses, donkeys, camels
- **Animal Health**: Vaccination schedules, disease symptoms, treatment, biosecurity

### Pest & Disease Management
- **Identification**: Pest and disease symptoms, lifecycle, damage patterns
- **Prevention**: Cultural practices, resistant varieties, biological control
- **Control**: Integrated Pest Management (IPM), chemical pesticides (safe use), organic methods
- **Specific Pests**: Aphids, armyworms, cutworms, termites, weevils, locusts
- **Specific Diseases**: Fungal (rust, blight, mildew), bacterial (bacterial wilt, leaf spot), viral (mosaic virus)

### Soil Health & Fertilization
- **Soil Testing**: pH levels, nutrient analysis, soil structure assessment
- **Nutrients**: NPK requirements, micronutrients, organic matter, soil amendments
- **Fertilizers**: Types (organic vs synthetic), application methods, timing, rates
- **Soil Conservation**: Erosion control, cover crops, mulching, conservation tillage
- **Composting**: Methods, materials, application, benefits

### Water Management & Irrigation
- **Irrigation Methods**: Drip, sprinkler, flood, furrow, overhead irrigation
- **Water Requirements**: Crop water needs, scheduling, efficiency
- **Water Sources**: Wells, boreholes, rivers, rainwater harvesting
- **Drought Management**: Water conservation, drought-resistant crops, mulching
- **Drainage**: Waterlogging prevention, drainage systems

### Weather & Climate
- **Seasonal Planning**: Planting calendars, weather patterns, climate zones
- **Weather Risks**: Frost protection, heat stress, wind damage, hail protection
- **Climate Adaptation**: Climate-smart agriculture, resilient varieties
- **Microclimate Management**: Windbreaks, shade management, micro-irrigation

### Market & Economics
- **Market Prices**: Current trends, price fluctuations, market timing
- **Value Addition**: Processing, packaging, branding, certification
- **Marketing Strategies**: Direct sales, cooperatives, online platforms
- **Financial Planning**: Budgeting, cost-benefit analysis, record-keeping
- **Access to Finance**: Loans, grants, insurance, credit facilities

### Sustainable & Organic Farming
- **Organic Certification**: Requirements, standards, transition period
- **Sustainable Practices**: Conservation agriculture, agroforestry, permaculture
- **Biodiversity**: Beneficial insects, pollinators, habitat conservation
- **Climate-smart Agriculture**: Carbon sequestration, renewable energy use
- **Circular Economy**: Waste recycling, by-product utilization

### Farm Machinery & Equipment
- **Equipment Selection**: Tractors, plows, harvesters, irrigation equipment
- **Maintenance**: Regular servicing, repair, troubleshooting
- **Safety**: Equipment safety, protective gear, accident prevention
- **Cost Analysis**: Purchase vs rental, operational costs, efficiency

### Agricultural Technology
- **Precision Agriculture**: GPS mapping, soil sensors, drone technology
- **Digital Tools**: Farm management software, mobile apps, data analytics
- **Automation**: Automated irrigation, feeding systems, monitoring
- **IoT Applications**: Smart farming, remote monitoring, data collection

### Regulations & Compliance
- **Food Safety**: HACCP, GAP standards, pesticide residue limits
- **Environmental Regulations**: Water use, waste management, protected areas
- **Labor Laws**: Worker rights, safety standards, fair wages
- **Certifications**: Organic, fair trade, GlobalGAP, local standards

### Post-Harvest & Value Addition
- **Storage**: Proper storage conditions, pest control, shelf life extension
- **Processing**: Drying, canning, freezing, packaging
- **Quality Control**: Grading, sorting, quality standards
- **Supply Chain**: Logistics, transportation, cold chain management

## Your Response Style:
- **Practical & Actionable**: Provide specific steps, quantities, timelines
- **Evidence-Based**: Use scientific principles and proven methods
- **Context-Aware**: Consider farm size, resources, climate, local conditions
- **Clear & Simple**: Avoid jargon, explain technical terms when used
- **Comprehensive**: Cover what, why, how, when, and potential risks
- **Adaptive**: Ask clarifying questions when information is missing

## When You Need More Information:
Ask about:
- Geographic location and climate zone
- Farm size and scale (smallholder, commercial)
- Specific crops or livestock
- Current challenges or problems
- Available resources (budget, equipment, labor)
- Experience level (beginner, experienced)

## Important Guidelines:
- Always prioritize safety (chemical safety, equipment safety, food safety)
- Recommend sustainable and environmentally friendly practices when possible
- Provide cost-effective solutions suitable for the farmer's situation
- Include both traditional and modern approaches when relevant
- Warn about potential risks and common mistakes
- Suggest reliable sources for additional information when needed

Your goal is to be the most helpful, accurate, and practical agricultural assistant possible."""
            
            # Build context-enhanced prompt with user information
            context_info = ""
            if context.get('crop'):
                context_info += f"\nCrop Type: {context['crop']}"
            if context.get('livestock'):
                context_info += f"\nLivestock Type: {context['livestock']}"
            if context.get('topic'):
                context_info += f"\nTopic: {context['topic'].replace('_', ' ').title()}"
            if context.get('timeframe'):
                context_info += f"\nTimeframe: {context['timeframe']}"
            
            # Add user context if available
            if session.user:
                context_info += f"\nUser Type: {session.user.user_type}"
                if session.farm:
                    context_info += f"\nFarm: {session.farm.name}"
                    if session.farm.location_lat and session.farm.location_lng:
                        context_info += f"\nFarm Location: {session.farm.location_lat}, {session.farm.location_lng}"
            
            # Use AI for all responses (not just templates)
            try:
                ai_service = MultiAIService()
                
                # Try with system prompt for better farming-specific responses
                enhanced_response = ai_service.query_gemini(
                    prompt=f"""{system_prompt}

Farmer's Question:{context_info}
{user_input}

Provide a helpful, practical response:""",
                    model_type='gemini'
                )
                
                if enhanced_response:
                    return enhanced_response.strip()
            except Exception as e:
                logger.warning(f"AI generation attempt failed, retrying with simpler prompt: {str(e)}")
                try:
                    # Fallback: simpler prompt
                    ai_service = MultiAIService()
                    fallback_response = ai_service.query_gemini(
                        prompt=f"As an agricultural expert, provide accurate and practical farming advice for this question:{context_info}\n\n{user_input}",
                        model_type='gemini'
                    )
                    if fallback_response:
                        return fallback_response.strip()
                except Exception as e2:
                    logger.error(f"AI fallback also failed: {str(e2)}")
            
            # Final fallback: use intent template if available
            if intent and intent.response_template:
                return intent.response_template
            
            return ChatbotService._get_fallback_response(user_input, context)
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return ChatbotService._get_fallback_response(user_input, context)
    
    @staticmethod
    def _get_fallback_response(user_input, context=None):
        """Return context-aware farming-specific fallback response when AI is unavailable"""
        if context is None:
            context = {}
        
        # Extract context from user input if not provided
        user_input_lower = user_input.lower()
        
        # Check if we have specific context to provide helpful answers
        if context.get('crop'):
            crop = context['crop']
            return ChatbotService._get_crop_specific_response(crop, user_input_lower, context)
        
        if context.get('livestock'):
            livestock = context['livestock']
            return ChatbotService._get_livestock_specific_response(livestock, user_input_lower, context)
        
        if context.get('topic'):
            topic = context['topic']
            return ChatbotService._get_topic_specific_response(topic, user_input_lower, context)
        
        # General helpful responses based on keywords
        if any(word in user_input_lower for word in ['help', 'what can you do', 'capabilities']):
            return "I'm FarmWise, your agricultural assistant! I can help with:\n\n• Crop production (planting, growing, harvesting)\n• Livestock management (feeding, health, breeding)\n• Pest and disease identification and treatment\n• Soil health and fertilization\n• Water management and irrigation\n• Weather and climate planning\n• Market prices and selling strategies\n• Organic and sustainable farming\n• Farm equipment and machinery\n• Agricultural technology and digital tools\n\nJust ask me anything about farming - you can also upload images of plants, pests, or diseases for analysis!"
        
        # Location-based response
        if context.get('has_location_query'):
            return "I can provide location-specific farming advice! Please tell me:\n• Your specific region or climate zone\n• What crops or livestock you're raising\n• Your main farming challenges\n\nThis will help me give you tailored recommendations for your area."
        
        # Default to more helpful response
        return f"I understand you're asking about: {user_input}\n\nTo give you the most helpful advice, please share:\n• What crop or livestock you're working with\n• Your location/climate region\n• What specific problem or question you have\n\nFor example: 'How do I prevent tomato blight in Muzarabani?' or 'When should I harvest maize in a tropical climate?'"
    
    @staticmethod
    def _get_crop_specific_response(crop, user_input_lower, context):
        """Provide crop-specific advice when AI is unavailable"""
        crop_advice = {
            'tomato': "For tomatoes in your region:\n\n• Planting: Start seeds 6-8 weeks before last frost, transplant after soil warms\n• Spacing: 2-3 feet between plants\n• Water: 1-2 inches per week, consistent moisture\n• Fertilizer: Balanced NPK at planting, side-dress with nitrogen when fruit sets\n• Common issues: Blossom end rot (calcium deficiency), early blight, aphids\n• Harvest: When fully colored and slightly soft\n\nFor specific problems like pests or diseases, please describe the symptoms or upload a photo.",
            'maize': "For maize cultivation:\n\n• Planting: After soil temperature reaches 15°C, 2-3 inches deep\n• Spacing: 8-12 inches between plants, 30-36 inches between rows\n• Water: 1-1.5 inches per week during critical growth stages\n• Fertilizer: Nitrogen-rich fertilizer at V6 stage, side-dress at tasseling\n• Common issues: Fall armyworm, maize streak virus, nutrient deficiencies\n• Harvest: When kernels are fully formed and dry\n\nFor specific advice about your location or problems, please provide more details.",
            'potato': "For potato growing:\n\n• Planting: Plant seed potatoes 4 inches deep, eyes up\n• Spacing: 12 inches apart, 30-36 inches between rows\n• Water: 1-2 inches per week, avoid waterlogging\n• Fertilizer: High phosphorus at planting, nitrogen during growth\n• Common issues: Late blight, Colorado potato beetle, scab\n• Harvest: When vines die back, cure before storage\n\nFor specific problems, please describe symptoms or upload images.",
            'beans': "For bean cultivation:\n\n• Planting: After last frost, 1 inch deep\n• Spacing: 4-6 inches between plants, support for pole beans\n• Water: 1 inch per week, consistent moisture\n• Fertilizer: Low nitrogen (fixes own), moderate phosphorus/potassium\n• Common issues: Bean beetles, rust, aphids\n• Harvest: When pods are firm but before seeds bulge\n\nFor specific advice, please provide more details about your situation.",
        }
        
        if crop in crop_advice:
            return crop_advice[crop]
        
        return f"For {crop} cultivation, I can provide specific advice on:\n• Planting time and methods\n• Spacing and soil requirements\n• Water and nutrient needs\n• Common pests and diseases\n• Harvesting and storage\n\nPlease let me know what specific aspect of {crop} farming you need help with, or describe any problems you're experiencing."
    
    @staticmethod
    def _get_livestock_specific_response(livestock, user_input_lower, context):
        """Provide livestock-specific advice when AI is unavailable"""
        livestock_advice = {
            'cattle': "For cattle management:\n\n• Feeding: Quality forage, supplement with grain as needed\n• Water: 10-15 gallons per day per animal\n• Health: Regular vaccination, deworming, hoof care\n• Breeding: Plan breeding season for optimal calf survival\n• Housing: Shelter from extreme weather, good ventilation\n\nFor specific issues like diseases, nutrition, or breeding, please provide more details.",
            'chicken': "For poultry management:\n\n• Feeding: Balanced layer/broiler feed, clean water always\n• Housing: 4 sq ft per bird, good ventilation, nest boxes\n• Health: Vaccination schedule, parasite control, biosecurity\n• Eggs: Collect daily, provide calcium supplement\n• Broilers: High-protein feed, 6-8 weeks to market weight\n\nFor specific problems, please describe symptoms or ask detailed questions.",
            'goat': "For goat management:\n\n• Feeding: Browse and forage, supplement with grain\n• Water: Clean water available 24/7\n• Health: CD&T vaccination, regular deworming, hoof trimming\n• Breeding: Does can breed at 7-12 months, gestation 5 months\n• Housing: Dry, well-ventilated shelter, secure fencing\n\nFor specific advice, please provide more details about your situation.",
        }
        
        if livestock in livestock_advice:
            return livestock_advice[livestock]
        
        return f"For {livestock} management, I can help with:\n• Feeding and nutrition\n• Health and disease prevention\n• Breeding and reproduction\n• Housing and facilities\n• Production management\n\nPlease let me know what specific aspect of {livestock} farming you need help with."
    
    @staticmethod
    def _get_topic_specific_response(topic, user_input_lower, context):
        """Provide topic-specific advice when AI is unavailable"""
        topic_advice = {
            'pest_disease': "For pest and disease management:\n\n• Prevention: Crop rotation, resistant varieties, proper spacing\n• Identification: Look for specific symptoms on leaves, stems, fruit\n• Treatment: Start with least toxic options (neem oil, insecticidal soap)\n• Chemicals: Use as last resort, follow label instructions\n• Timing: Treat early in infestation, prevent spread\n\nFor specific identification, please describe symptoms or upload a photo of the affected plant.",
            'soil_health': "For soil health management:\n\n• Testing: Test soil every 2-3 years for pH and nutrients\n• pH: Most crops prefer 6.0-7.0, adjust with lime or sulfur\n• Organic matter: Add compost, manure, cover crops\n• Nutrients: Balance NPK based on soil test and crop needs\n• Conservation: Reduce tillage, use mulch, prevent erosion\n\nFor specific soil problems, please share your soil test results or describe issues.",
            'water_management': "For water management:\n\n• Irrigation: Drip irrigation is most efficient (90% efficiency)\n• Scheduling: Water early morning, 1-2 inches per week for most crops\n• Drought: Choose drought-resistant varieties, mulch heavily\n• Drainage: Ensure good drainage to prevent waterlogging\n• Conservation: Rainwater harvesting, soil moisture monitoring\n\nFor specific irrigation advice, please describe your setup and climate.",
            'market_price': "For market and pricing:\n\n• Timing: Sell when demand is high (holidays, off-season)\n• Quality: Higher quality commands premium prices\n• Direct sales: Farmers markets, CSA, online platforms get better margins\n• Storage: Proper storage extends selling window\n• Information: Monitor local market trends and prices\n\nFor specific market advice, please share your location and what you're selling.",
        }
        
        if topic in topic_advice:
            return topic_advice[topic]
        
        return f"I can help with {topic.replace('_', ' ')} topics. Please provide more specific details about your situation so I can give you targeted advice."
    
    @staticmethod
    def process_message(session_id, user_input, user=None, image_file=None):
        """Process user message and generate bot response with optional image support"""
        try:
            session = ChatSession.objects.get(id=session_id)
            
            # Recognize intent
            intent, confidence = ChatbotService.recognize_intent(user_input)
            
            # Extract context
            context = ChatbotService.extract_context(user_input, session)
            
            # Store user message
            user_message = ChatMessage.objects.create(
                session=session,
                message_type='user',
                content=user_input,
                intent=intent,
                confidence_score=confidence,
                metadata=context
            )
            
            # Process image if provided
            image_analysis = None
            if image_file:
                image_analysis = ChatbotService.process_image(image_file, context)
                if image_analysis:
                    context['image_analysis'] = image_analysis
            
            # Generate response with conversation history
            response_text = ChatbotService.generate_response_with_history(
                intent, user_input, session, context, image_analysis
            )
            
            # Store bot response
            bot_message = ChatMessage.objects.create(
                session=session,
                message_type='bot',
                content=response_text,
                intent=intent,
                confidence_score=confidence
            )
            
            # Update session message count
            session.message_count = session.messages.count()
            session.save()
            
            logger.info(f"Processed message in session {session_id}")
            
            return {
                'user_message_id': user_message.id,
                'bot_message_id': bot_message.id,
                'response': response_text,
                'intent': intent.intent_name if intent else None,
                'confidence': confidence,
                'image_analysis': image_analysis
            }
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def process_image(image_file, context):
        """Process image using AI for agricultural analysis"""
        try:
            from core.services.multi_ai_service import MultiAIService
            
            ai_service = MultiAIService()
            result = ai_service.detect_pest(image_file)
            
            if result.get('success'):
                return {
                    'pest_name': result.get('pest_name'),
                    'confidence': result.get('confidence'),
                    'treatment': result.get('treatment'),
                    'provider': result.get('provider')
                }
            return None
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return None
    
    @staticmethod
    def generate_response_with_history(intent, user_input, session, context=None, image_analysis=None):
        """Generate response with conversation history like ChatGPT/Claude"""
        try:
            if context is None:
                context = {}
            
            # Get conversation history (last 10 messages for context)
            recent_messages = ChatMessage.objects.filter(
                session=session
            ).order_by('-created_at')[:10]
            
            # Build conversation history string
            conversation_history = ""
            if recent_messages.exists():
                for msg in reversed(recent_messages):
                    if msg.message_type == 'user':
                        conversation_history += f"User: {msg.content}\n"
                    else:
                        conversation_history += f"Assistant: {msg.content}\n"
            
            # Build comprehensive system prompt with agricultural expertise
            system_prompt = """You are FarmWise, an expert agricultural AI assistant with comprehensive knowledge across all aspects of farming and agriculture. You provide accurate, practical, science-based advice to help farmers, agricultural students, researchers, and anyone interested in farming.

## Your Expertise Covers:

### Crop Production & Management
- **Planting**: Seed selection, planting depth, spacing, timing, seed treatment, germination
- **Growing**: Crop nutrition, growth stages, pruning, training, crop rotation, intercropping
- **Harvesting**: Harvest timing, methods, post-harvest handling, storage, preservation
- **Specific Crops**: Cereals (maize, wheat, rice, sorghum, millet), legumes (beans, soybeans, groundnuts), vegetables (tomatoes, potatoes, onions, cabbage, kale), fruits (bananas, mangoes, citrus, avocados), cash crops (coffee, tea, sugarcane, cotton)

### Livestock & Animal Husbandry
- **Cattle**: Breeding, feeding, health management, milk production, beef production
- **Small Ruminants**: Sheep and goat management, breeding, health, meat/milk production
- **Poultry**: Chicken (layers/broilers), ducks, turkeys - housing, feeding, disease prevention
- **Other Animals**: Pigs, fish farming, beekeeping, horses, donkeys, camels
- **Animal Health**: Vaccination schedules, disease symptoms, treatment, biosecurity

### Pest & Disease Management
- **Identification**: Pest and disease symptoms, lifecycle, damage patterns
- **Prevention**: Cultural practices, resistant varieties, biological control
- **Control**: Integrated Pest Management (IPM), chemical pesticides (safe use), organic methods
- **Specific Pests**: Aphids, armyworms, cutworms, termites, weevils, locusts
- **Specific Diseases**: Fungal (rust, blight, mildew), bacterial (bacterial wilt, leaf spot), viral (mosaic virus)

### Soil Health & Fertilization
- **Soil Testing**: pH levels, nutrient analysis, soil structure assessment
- **Nutrients**: NPK requirements, micronutrients, organic matter, soil amendments
- **Fertilizers**: Types (organic vs synthetic), application methods, timing, rates
- **Soil Conservation**: Erosion control, cover crops, mulching, conservation tillage
- **Composting**: Methods, materials, application, benefits

### Water Management & Irrigation
- **Irrigation Methods**: Drip, sprinkler, flood, furrow, overhead irrigation
- **Water Requirements**: Crop water needs, scheduling, efficiency
- **Water Sources**: Wells, boreholes, rivers, rainwater harvesting
- **Drought Management**: Water conservation, drought-resistant crops, mulching
- **Drainage**: Waterlogging prevention, drainage systems

### Weather & Climate
- **Seasonal Planning**: Planting calendars, weather patterns, climate zones
- **Weather Risks**: Frost protection, heat stress, wind damage, hail protection
- **Climate Adaptation**: Climate-smart agriculture, resilient varieties
- **Microclimate Management**: Windbreaks, shade management, micro-irrigation

### Market & Economics
- **Market Prices**: Current trends, price fluctuations, market timing
- **Value Addition**: Processing, packaging, branding, certification
- **Marketing Strategies**: Direct sales, cooperatives, online platforms
- **Financial Planning**: Budgeting, cost-benefit analysis, record-keeping
- **Access to Finance**: Loans, grants, insurance, credit facilities

### Sustainable & Organic Farming
- **Organic Certification**: Requirements, standards, transition period
- **Sustainable Practices**: Conservation agriculture, agroforestry, permaculture
- **Biodiversity**: Beneficial insects, pollinators, habitat conservation
- **Climate-smart Agriculture**: Carbon sequestration, renewable energy use
- **Circular Economy**: Waste recycling, by-product utilization

### Farm Machinery & Equipment
- **Equipment Selection**: Tractors, plows, harvesters, irrigation equipment
- **Maintenance**: Regular servicing, repair, troubleshooting
- **Safety**: Equipment safety, protective gear, accident prevention
- **Cost Analysis**: Purchase vs rental, operational costs, efficiency

### Agricultural Technology
- **Precision Agriculture**: GPS mapping, soil sensors, drone technology
- **Digital Tools**: Farm management software, mobile apps, data analytics
- **Automation**: Automated irrigation, feeding systems, monitoring
- **IoT Applications**: Smart farming, remote monitoring, data collection

### Regulations & Compliance
- **Food Safety**: HACCP, GAP standards, pesticide residue limits
- **Environmental Regulations**: Water use, waste management, protected areas
- **Labor Laws**: Worker rights, safety standards, fair wages
- **Certifications**: Organic, fair trade, GlobalGAP, local standards

### Post-Harvest & Value Addition
- **Storage**: Proper storage conditions, pest control, shelf life extension
- **Processing**: Drying, canning, freezing, packaging
- **Quality Control**: Grading, sorting, quality standards
- **Supply Chain**: Logistics, transportation, cold chain management

## Your Response Style:
- **Practical & Actionable**: Provide specific steps, quantities, timelines
- **Evidence-Based**: Use scientific principles and proven methods
- **Context-Aware**: Consider farm size, resources, climate, local conditions
- **Clear & Simple**: Avoid jargon, explain technical terms when used
- **Comprehensive**: Cover what, why, how, when, and potential risks
- **Adaptive**: Ask clarifying questions when information is missing
- **Conversational**: Maintain context from previous messages, reference earlier discussion
- **Helpful**: Go beyond basic answers to provide truly useful guidance

## When You Need More Information:
Ask about:
- Geographic location and climate zone
- Farm size and scale (smallholder, commercial)
- Specific crops or livestock
- Current challenges or problems
- Available resources (budget, equipment, labor)
- Experience level (beginner, experienced)

## Important Guidelines:
- Always prioritize safety (chemical safety, equipment safety, food safety)
- Recommend sustainable and environmentally friendly practices when possible
- Provide cost-effective solutions suitable for the farmer's situation
- Include both traditional and modern approaches when relevant
- Warn about potential risks and common mistakes
- Suggest reliable sources for additional information when needed
- Reference previous conversation when relevant to maintain context
- If the user asks follow-up questions, build on your previous responses

Your goal is to be the most helpful, accurate, and practical agricultural assistant possible, similar to ChatGPT or Claude but specialized for farming."""
            
            # Build context-enhanced prompt with user information
            context_info = ""
            if context.get('crop'):
                context_info += f"\nCrop Type: {context['crop']}"
            if context.get('livestock'):
                context_info += f"\nLivestock Type: {context['livestock']}"
            if context.get('topic'):
                context_info += f"\nTopic: {context['topic'].replace('_', ' ').title()}"
            if context.get('timeframe'):
                context_info += f"\nTimeframe: {context['timeframe']}"
            
            # Add user context if available
            if session.user:
                context_info += f"\nUser Type: {session.user.user_type}"
                if session.farm:
                    context_info += f"\nFarm: {session.farm.name}"
                    if session.farm.location_lat and session.farm.location_lng:
                        context_info += f"\nFarm Location: {session.farm.location_lat}, {session.farm.location_lng}"
            
            # Add image analysis if available
            image_context = ""
            if image_analysis:
                image_context = f"\n\nIMAGE ANALYSIS RESULTS:\n"
                image_context += f"- Detected: {image_analysis.get('pest_name', 'Unknown')}\n"
                image_context += f"- Confidence: {image_analysis.get('confidence', 0)}%\n"
                image_context += f"- Treatment: {image_analysis.get('treatment', 'N/A')}\n"
                image_context += f"- Analysis by: {image_analysis.get('provider', 'AI')}\n"
            
            # Build full prompt with conversation history
            full_prompt = f"""{system_prompt}

CONVERSATION HISTORY:
{conversation_history if conversation_history else "This is the start of our conversation."}

CURRENT CONTEXT:{context_info}{image_context}

Farmer's Question:
{user_input}

Provide a helpful, practical response that builds on our conversation when relevant:"""
            
            # Use AI for all responses with conversation history
            try:
                ai_service = MultiAIService()
                
                # Try with enhanced prompt for better ChatGPT-like responses
                enhanced_response = ai_service.query_gemini(
                    prompt=full_prompt,
                    model_type='gemini'
                )
                
                if enhanced_response:
                    return enhanced_response.strip()
            except Exception as e:
                logger.warning(f"AI generation attempt failed, retrying with simpler prompt: {str(e)}")
                try:
                    # Fallback: simpler prompt without history
                    ai_service = MultiAIService()
                    fallback_response = ai_service.query_gemini(
                        prompt=f"As an agricultural expert, provide accurate and practical farming advice for this question:{context_info}{image_context}\n\n{user_input}",
                        model_type='gemini'
                    )
                    if fallback_response:
                        return fallback_response.strip()
                except Exception as e2:
                    logger.error(f"AI fallback also failed: {str(e2)}")
            
            # Final fallback: use intent template if available
            if intent and intent.response_template:
                return intent.response_template
            
            return ChatbotService._get_fallback_response(user_input, context)
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return ChatbotService._get_fallback_response(user_input, context)
    
    @staticmethod
    def save_message_feedback(message_id, rating, comment='', tags=None):
        """Save feedback on a chatbot response"""
        try:
            message = ChatMessage.objects.get(id=message_id)
            
            feedback, created = ChatFeedback.objects.get_or_create(
                message=message,
                defaults={
                    'rating': rating,
                    'comment': comment,
                    'tags': tags or [],
                    'user_submitted': True
                }
            )
            
            if not created:
                feedback.rating = rating
                feedback.comment = comment
                feedback.tags = tags or []
                feedback.save()
            
            # Update response usage if applicable
            if message.intent and message.message_type == 'bot':
                try:
                    response = ChatResponse.objects.filter(
                        keywords__icontains=message.intent.intent_name
                    ).first()
                    if response:
                        response.usage_count += 1
                        response.save()
                except:
                    pass
            
            return feedback
        
        except Exception as e:
            logger.error(f"Error saving feedback: {str(e)}")
            return None
    
    @staticmethod
    def get_session_history(session_id):
        """Get all messages in a session"""
        try:
            session = ChatSession.objects.get(id=session_id)
            messages = session.messages.all().order_by('created_at')
            return list(messages)
        except Exception as e:
            logger.error(f"Error getting session history: {str(e)}")
            return []
    
    @staticmethod
    def search_responses(query):
        """Search for previously stored responses"""
        try:
            query_lower = query.lower()
            responses = ChatResponse.objects.filter(
                Q(question__icontains=query_lower) | 
                Q(answer__icontains=query_lower) |
                Q(keywords__icontains=query_lower)
            ).filter(is_approved=True)
            return responses
        except Exception as e:
            logger.error(f"Error searching responses: {str(e)}")
            return []
    
    @staticmethod
    def calculate_session_statistics():
        """Calculate daily chatbot statistics"""
        try:
            today = timezone.now().date()
            
            sessions = ChatSession.objects.filter(started_at__date=today)
            messages = ChatMessage.objects.filter(created_at__date=today)
            feedback = ChatFeedback.objects.filter(created_at__date=today)
            
            total_sessions = sessions.count()
            total_messages = messages.count()
            avg_messages = (total_messages / total_sessions) if total_sessions > 0 else 0
            
            # Calculate average satisfaction
            ratings = feedback.filter(message__message_type='bot').values_list('rating', flat=True)
            rating_scores = {
                'excellent': 5, 'good': 4, 'neutral': 3, 'poor': 2, 'unhelpful': 1
            }
            scores = [rating_scores.get(r, 0) for r in ratings]
            avg_satisfaction = (sum(scores) / len(scores)) if scores else 0
            
            # Most common intent
            intent_stats = messages.filter(intent__isnull=False).values('intent__intent_name').count()
            most_common = messages.filter(intent__isnull=False).values_list(
                'intent__intent_name', flat=True
            ).first()
            
            # Unique users
            unique_users = sessions.values('user').distinct().count()
            
            # Resolved queries (with helpful feedback)
            resolved = feedback.filter(rating__in=['excellent', 'good']).count()
            
            stats, created = ChatStatistics.objects.get_or_create(
                date=today,
                defaults={
                    'total_sessions': total_sessions,
                    'total_messages': total_messages,
                    'avg_messages_per_session': avg_messages,
                    'avg_satisfaction': avg_satisfaction,
                    'most_common_intent': most_common or 'N/A',
                    'unique_users': unique_users,
                    'resolved_queries': resolved
                }
            )
            
            return stats
        
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return None
