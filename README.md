# Event Content Generator 

Professional event content generator using OpenAI's GPT-3.5-turbo and DALL·E 3 with advanced prompt engineering, cost optimization, and comprehensive content generation capabilities.

## Features

### Core Functionality
- **Complete Event Content**: Generate titles, descriptions, flyers/banners, FAQs, and refund policies
- **Sequential Workflow**: Generate content step-by-step with user selection and customization at each stage
- **Content Customization**: Edit, mix, or create custom content for every component
- **Advanced Prompt Engineering**: Few-shot learning, role-based prompting, dynamic styling, and fuzzy correction
- **Cost Optimization**: Three modes (Economy, Balanced, Premium) with intelligent cost management

### Content Generation Modules
- **Titles**: Creative, unique event titles (3-6 words) with smart retry mechanism and fallback system
- **Descriptions**: Compelling event descriptions up to 2000 characters with length optimization
- **Flyers/Banners**: Professional event flyers using DALL·E 3 with multiple aspect ratios (Square, Wide, Tall)
- **FAQs**: At least 5 relevant questions and answers tailored to event type and category
- **Refund Policies**: Clear, professional refund policies appropriate for different event types

### Smart Features
- **Optimization Suggestions**: AI-powered recommendations for best category/event type/tone combinations
- **Fuzzy Correction**: Intelligent typo correction and suggestions for custom inputs
- **Professional Summary**: Bullet-point formatted complete event package with download options
- **Analytics Dashboard**: Real-time token usage, cost tracking, and performance metrics for each module

### User Experience
- **Clean UI**: Professional Streamlit interface with modern styling and intuitive workflow
- **Content Selection**: Choose from generated options, edit existing content, or create custom content
- **Smart Suggestions**: Get optimization tips and pro recommendations based on your selections
- **Complete Integration**: All modules work together seamlessly with content inheritance options

## Quick Start

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up API key:**
```bash
echo OPENAI_API_KEY=your_openai_api_key_here > .env
```

3. **Run the application:**
```bash
streamlit run app.py
```

### Streamlit Cloud Deployment

1. **Fork/Clone this repository**
2. **Deploy on Streamlit Cloud:**
   - Visit: https://share.streamlit.io/
   - Connect your GitHub account
   - Select this repository
   - Set main file: `app.py`
   
3. **Add API Key in Streamlit Secrets:**
   - Go to app settings → Secrets
   - Add: `OPENAI_API_KEY = "your_openai_api_key_here"`
   - Get your key from: https://platform.openai.com/api-keys

## Cost Optimization

### Available Modes
- **Economy**: Maximum cost savings, efficient quality (~$0.0002 per generation)
- **Balanced**: Optimal cost-quality balance (~$0.0003 per generation)
- **Premium**: Best quality with advanced features (~$0.0005 per generation)

### Analytics Provided
- Token usage (prompt, completion, total)
- Generation time and cost estimation
- Model information and prompt previews
- Performance metrics for each module

## CLI Services

### Title Generation
```bash
python title_service.py --category "Technology" --event_type "Conference" --tone "Professional" --num_titles 3 --context "AI focus"
```

### Description Generation
```bash
python description_service.py --title "AI Innovation Summit" --category "Technology" --event_type "Conference" --tone "Professional" --max_chars 1500 --context "networking emphasis"
```

### Flyer/Banner Generation
```bash
python flyer_service.py --title "AI Innovation Summit" --description "A premier event for AI leaders and innovators." --category "Technology" --event_type "Conference" --tone "Professional" --cost_mode premium --context "Focus on networking and future trends"
```

### FAQ & Refund Policy Generation
```bash
python faq_refund_service.py --title "AI Innovation Summit" --description "A premier event for AI leaders and innovators." --category "Technology" --event_type "Conference" --tone "Professional" --context "Focus on networking and future trends" --cost_mode balanced
```

## Architecture

### Core Files
- `event_llm_core.py` - Central LLM logic, cost optimization, and core generation functions
- `app.py` - Streamlit interface with sequential workflow and content customization
- `title_service.py` - CLI microservice for title generation
- `description_service.py` - CLI microservice for description generation
- `flyer_service.py` - CLI microservice for flyer/banner generation
- `faq_refund_service.py` - CLI microservice for FAQ and refund policy generation

### Design Principles
- **Modular Architecture**: Clean separation between core logic and UI
- **Sequential Workflow**: Step-by-step content generation with user control
- **Content Inheritance**: Use previous selections or customize each step independently
- **Professional Output**: Consistent quality and formatting across all modules

## API Reference

### Supported Parameters
- **Categories**: Technology, Business, Education, Health, Entertainment, Sports, Arts & Culture, Other (with custom input)
- **Event Types**: Conference, Workshop, Seminar, Webinar, Festival, Exhibition, Meetup, Gala, Other (with custom input)
- **Tones**: Professional, Casual, Formal, Creative, Premium, Innovative, Friendly, Corporate, Playful, Other (with custom input)
- **Cost Modes**: economy, balanced, premium
- **Limits**: Titles (1-5, 3-6 words each), Descriptions (100-2000 characters), Images (multiple aspect ratios)

### Response Format
All generation functions return content and detailed logs:
```python
titles, logs = generate_titles(category, event_type, tone, num_titles, context, cost_mode)
description, logs = generate_description(title, category, event_type, tone, context, max_chars, cost_mode)
image_url, logs = generate_flyer_image(title, description, category, event_type, tone, context, cost_mode, size)
faqs, refund_policy, logs = generate_faqs_and_refund_policy(title, description, category, event_type, tone, context, cost_mode)
```

## Key Features

### Smart Optimization
- **Pro Tips**: Context-aware suggestions for best results based on your selections
- **Optimization Suggestions**: Recommended settings for different event types
- **Fuzzy Correction**: Intelligent suggestions when you type custom categories, event types, or tones

### Content Workflow
1. **Generate Titles** → Select/Edit/Create custom title
2. **Generate Description** → Use inherited settings or customize parameters
3. **Generate Flyer** → Professional visual design with DALL·E 3
4. **Generate FAQs & Refund Policy** → Comprehensive Q&A and policies
5. **Complete Summary** → Professional bullet-point format with download options

### Professional Output
- **Event Summary**: Clean, professional format with bullet points
- **Download Options**: Individual components and complete package
- **Analytics**: Detailed metrics for each generation step
- **Quality Assurance**: Robust error handling and fallback systems

---

**Ready for Production**: This system provides a complete, professional event content generation solution with advanced AI capabilities and user-friendly interface.