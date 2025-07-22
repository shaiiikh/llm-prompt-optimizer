# EC - Title & Desc Gen

Professional event title and description generator using GPT-3.5-turbo with advanced prompt engineering, cost optimization, and comprehensive testing capabilities.

## Features

### Core Functionality
- **Independent Generation**: Separate parameters for titles and descriptions
- **Title Management**: Generate, select, edit, or create custom titles
- **Advanced Prompt Engineering**: Few-shot learning, role-based prompting, hyperparameter optimization
- **Cost Optimization**: Three modes (Economy, Balanced, Premium) with up to 58% cost savings

### Quality & Testing
- **A/B Testing Suite**: Comprehensive testing of all input combinations and edge cases
- **Input Validation**: Error handling with fuzzy correction for typos
- **Quality Metrics**: Efficiency scoring, utilization tracking, performance analytics
- **Professional Output**: 3-6 word titles, formatted descriptions up to 2000 characters

### User Experience
- **Clean UI**: Professional Streamlit interface with dark mode compatibility
- **Real-time Analytics**: Token usage, cost tracking, timing metrics in sidebar
- **Custom Inputs**: "Other" option with instant custom input boxes
- **Smart Suggestions**: Optimization recommendations based on selections

## Quick Start

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

## Cost Optimization

### Available Modes
- **Economy**: 58% cost savings, basic quality (~$0.0002 per cycle)
- **Balanced**: 37% cost savings, optimal quality (~$0.0003 per cycle)
- **Premium**: Best quality, similar cost (~$0.0005 per cycle)

### Analytics Provided
- Cost per title/character
- Efficiency scores (value per dollar)
- Target utilization percentages  
- Performance comparisons across modes

## Testing & Quality Assurance

### Comprehensive Test Coverage
- Valid input combinations
- Edge cases and boundary conditions
- Invalid input handling
- False positive/negative detection
- Performance and cost validation

### Run Tests
Click "Run A/B Tests" in the interface or use CLI:
```bash
python -c "from event_llm_core import run_comprehensive_tests; print(run_comprehensive_tests())"
```

## CLI Services

### Title Generation
```bash
python title_service.py --category "Technology" --event_type "Conference" --tone "Professional" --num_titles 3 --context "AI focus"
```

### Description Generation
```bash
python description_service.py --title "AI Innovation Summit" --category "Technology" --event_type "Conference" --tone "Professional" --max_chars 1500 --context "networking emphasis"
```

## Architecture

### Core Files
- `event_llm_core.py` - Central LLM logic, cost optimization, testing framework
- `app.py` - Streamlit interface with advanced UI features
- `title_service.py` - CLI microservice for title generation with logging
- `description_service.py` - CLI microservice for description generation with logging

### Design Principles
- DRY principle implementation
- Modular architecture
- Comprehensive error handling
- Professional code standards

## API Reference

### Parameters
- **Category**: Technology, Business, Education, Health, Entertainment, Sports, Arts & Culture, Other
- **Event Type**: Conference, Workshop, Seminar, Webinar, Festival, Exhibition, Meetup, Other
- **Tone**: Professional, Casual, Formal, Creative, Premium, Innovative, Friendly, Corporate, Other
- **Cost Mode**: economy, balanced, premium
- **Context**: Optional additional context (up to 200 characters)
- **Limits**: Titles (3-6 words), Descriptions (100-2000 characters)

### Response Format
```python
titles, logs = generate_titles(category, event_type, tone, num_titles, context, cost_mode)
description, logs = generate_description(title, category, event_type, tone, context, max_chars, cost_mode)
```

## Production Deployment

### Flask Integration Ready
- Separate title/description endpoints
- Independent parameter handling
- Comprehensive logging and analytics
- Cost tracking and optimization
- Error handling and validation

### Performance Metrics
- Average response time: <3 seconds
- Cost efficiency: Up to 58% savings in economy mode
- Quality consistency: Advanced prompt engineering ensures reliable output
- Scalability: Stateless design for horizontal scaling

Built by Ash