from openai import OpenAI
import json
import os
import time
from dotenv import load_dotenv
from difflib import get_close_matches
import logging

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_json_output(raw):
    raw = raw.strip()
    if raw.startswith('```json'):
        raw = raw[len('```json'):].strip()
    if raw.startswith('```'):
        raw = raw[len('```'):].strip()
    if raw.endswith('```'):
        raw = raw[:-3].strip()
    return raw

def estimate_cost(prompt_tokens, completion_tokens):
    input_cost = 0.0005 * (prompt_tokens / 1000)
    output_cost = 0.0015 * (completion_tokens / 1000)
    return input_cost + output_cost

def count_tokens(text):
    return len(text.split())

def fuzzy_correct(user_input, valid_options):
    matches = get_close_matches(user_input, valid_options, n=1, cutoff=0.75)
    if matches:
        return matches[0]
    return user_input

def get_title_examples(category, event_type, tone):
    examples = {
        ("Technology", "Conference", "Professional"): ["Tech Leadership Summit", "Digital Innovation Forum", "Future Systems Expo"],
        ("Technology", "Workshop", "Creative"): ["Code & Create Lab", "Innovation Studio", "Digital Makers Hub"],
        ("Business", "Conference", "Professional"): ["Business Growth Summit", "Leadership Excellence Forum", "Strategic Success Conference"],
        ("Business", "Seminar", "Formal"): ["Executive Mastery Series", "Strategic Leadership Institute", "Business Excellence Summit"],
        ("Education", "Conference", "Innovative"): ["Learning Revolution Summit", "Educational Innovation Forum", "Teaching Excellence Expo"]
    }
    
    key = (category, event_type, tone)
    if key in examples:
        return examples[key]
    
    return [f"{category} Excellence Summit", f"{event_type} Innovation Forum", f"Advanced {category} Workshop"]

def validate_inputs(category, event_type, tone, num_titles=3, context=None):
    errors = []
    warnings = []
    
    if not category or category == "Select event category":
        errors.append("Category is required")
    if not event_type or event_type == "Select event type":
        errors.append("Event type is required")
    if not tone or tone == "Select tone of event":
        errors.append("Tone is required")
    
    if num_titles < 1 or num_titles > 5:
        warnings.append(f"Number of titles ({num_titles}) should be between 1-5")
    
    if context and len(context) > 200:
        warnings.append("Context is very long - may increase costs")
    
    logger.info(f"Input validation - Errors: {len(errors)}, Warnings: {len(warnings)}")
    return errors, warnings

def generate_titles(category, event_type, tone, num_titles=5, context=None, cost_mode="balanced"):
    logger.info(f"Generating titles: {category}/{event_type}/{tone}, count={num_titles}, mode={cost_mode}")
    
    errors, warnings = validate_inputs(category, event_type, tone, num_titles, context)
    if errors:
        return [], {"errors": errors, "warnings": warnings}
    
    num_titles = max(1, min(int(num_titles), 5))
    
    if cost_mode == "economy":
        system_msg = f"Generate {num_titles} creative {tone.lower()} event titles for {category} {event_type}. 3-6 words each, no colons. JSON format."
        user_msg = f"Create {num_titles} titles for {category} {event_type} ({tone})"
        max_tokens = 8 * num_titles + 20
        temperature = 0.7
    elif cost_mode == "premium":
        examples = get_title_examples(category, event_type, tone)
        examples_str = ", ".join(examples[:2])
        context_str = f" Context: {context}" if context else ""
        
        system_msg = f"""Expert event marketer. Generate {num_titles} compelling {tone.lower()} titles for {category} {event_type}.
Requirements: 3-6 words, memorable, actionable. Examples: {examples_str}
Format: JSON array{context_str}"""
        
        user_msg = f"Generate {num_titles} exceptional titles for {category} {event_type} with {tone} tone{context_str}"
        max_tokens = 15 * num_titles + 50
        temperature = 0.8
    else:  # balanced
        examples = get_title_examples(category, event_type, tone)
        context_str = f" Focus: {context}" if context else ""
        
        system_msg = f"""Professional event title generator. Create {num_titles} {tone.lower()} titles for {category} {event_type}.
- Length: 3-6 words
- Style: {tone.lower()}, memorable
- Format: JSON array
Examples: {examples[0]}, {examples[1]}{context_str}"""
        
        user_msg = f"Generate {num_titles} titles: {category} {event_type} ({tone}){context_str}"
        max_tokens = 12 * num_titles + 30
        temperature = 0.75
    
    start = time.time()
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.3
        )
        
        result = response.choices[0].message.content.strip()
        logger.info(f"Raw response length: {len(result)} chars")
        
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return [], {"error": str(e)}
    
    cleaned = clean_json_output(result)
    titles = []
    
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            titles = [str(t).strip() for t in parsed if isinstance(t, str) and t.strip()]
            titles = [t for t in titles if 3 <= len(t.split()) <= 6]
    except Exception as e:
        logger.warning(f"JSON parsing failed: {e}, attempting fallback")
        lines = result.replace('[', '').replace(']', '').replace('"', '').split(',')
        for line in lines:
            clean = line.strip().strip('"').strip("'").strip('-').strip('1234567890.').strip()
            if clean and 3 <= len(clean.split()) <= 6 and clean not in titles:
                titles.append(clean)
                if len(titles) >= num_titles:
                    break
    
    if len(titles) < num_titles:
        for i in range(len(titles), num_titles):
            titles.append(f"Premium {category} {event_type}")
    
    end = time.time()
    prompt_tokens = count_tokens(system_msg) + count_tokens(user_msg)
    completion_tokens = count_tokens(result)
    total_tokens = prompt_tokens + completion_tokens
    cost = estimate_cost(prompt_tokens, completion_tokens)
    
    efficiency_score = len(titles) / cost if cost > 0 else 0
    
    logs = {
        "Prompt tokens": prompt_tokens,
        "Completion tokens": completion_tokens,
        "Total tokens": total_tokens,
        "Time taken (s)": round(end - start, 2),
        "Estimated cost ($)": f"${cost:.5f}",
        "Cost per title": f"${cost/len(titles):.6f}" if titles else "$0",
        "Efficiency score": round(efficiency_score * 1000, 2),
        "Cost mode": cost_mode,
        "Warnings": warnings
    }
    
    logger.info(f"Generated {len(titles)} titles, cost: ${cost:.5f}")
    return titles[:num_titles], logs

def generate_description(title, category, event_type, tone, context=None, max_chars=2000, cost_mode="balanced"):
    logger.info(f"Generating description: {title}, mode={cost_mode}, max_chars={max_chars}")
    
    max_chars = max(100, min(int(max_chars), 2000))
    
    if cost_mode == "economy":
        system_msg = f"Write compelling {tone.lower()} description for '{title}' - {category} {event_type}. ~{max_chars} chars. Include benefits and call-to-action."
        user_msg = f"Description for: {title} ({category} {event_type}, {tone})"
        max_tokens = int(max_chars/3)
        temperature = 0.7
    elif cost_mode == "premium":
        context_str = f" Focus: {context}" if context else ""
        system_msg = f"""Expert copywriter. Write compelling {max_chars}-char description for '{title}' - {tone.lower()} {event_type} in {category}.
Structure: Hook → Problem → Solution → Benefits → CTA
Tone: {tone.lower()}, persuasive, action-oriented{context_str}"""
        
        user_msg = f"Write description for '{title}' ({category} {event_type}, {tone}). Target: {max_chars} chars{context_str}"
        max_tokens = int(max_chars/1.8)
        temperature = 0.75
    else:  # balanced
        context_str = f" Focus: {context}" if context else ""
        system_msg = f"""Professional copywriter. Create engaging {tone.lower()} description for '{title}' - {category} {event_type}.
Length: ~{max_chars} characters
Include: value proposition, benefits, call-to-action
Style: {tone.lower()}, compelling{context_str}"""
        
        user_msg = f"Write description: '{title}' ({category} {event_type}, {tone}){context_str}"
        max_tokens = int(max_chars/2.2)
        temperature = 0.72
    
    start = time.time()
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.3
        )
        
        description = response.choices[0].message.content.strip()
        logger.info(f"Generated description length: {len(description)} chars")
        
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return "", {"error": str(e)}
    
    end = time.time()
    
    prompt_tokens = count_tokens(system_msg) + count_tokens(user_msg)
    completion_tokens = count_tokens(description)
    total_tokens = prompt_tokens + completion_tokens
    cost = estimate_cost(prompt_tokens, completion_tokens)
    too_short = len(description) < int(0.6 * max_chars)
    
    char_efficiency = len(description) / cost if cost > 0 else 0
    
    logs = {
        "Prompt tokens": prompt_tokens,
        "Completion tokens": completion_tokens,
        "Total tokens": total_tokens,
        "Time taken (s)": round(end - start, 2),
        "Estimated cost ($)": f"${cost:.5f}",
        "Cost per char": f"${cost/len(description):.8f}" if description else "$0",
        "Char efficiency": round(char_efficiency, 2),
        "Target utilization": f"{len(description)/max_chars*100:.1f}%",
        "Cost mode": cost_mode,
        "Shorter than requested": too_short
    }
    
    return description[:max_chars], logs

def run_comprehensive_tests():
    test_cases = [
        # Valid cases
        {"category": "Technology", "event_type": "Conference", "tone": "Professional", "expected": "success"},
        {"category": "Business", "event_type": "Workshop", "tone": "Casual", "expected": "success"},
        {"category": "Education", "event_type": "Seminar", "tone": "Formal", "expected": "success"},
        
        # Edge cases
        {"category": "Other", "event_type": "Meetup", "tone": "Creative", "expected": "success"},
        {"category": "Technology", "event_type": "Conference", "tone": "Professional", "num_titles": 1, "expected": "success"},
        {"category": "Technology", "event_type": "Conference", "tone": "Professional", "num_titles": 5, "expected": "success"},
        
        # Invalid cases
        {"category": "", "event_type": "Conference", "tone": "Professional", "expected": "error"},
        {"category": "Technology", "event_type": "", "tone": "Professional", "expected": "error"},
        {"category": "Technology", "event_type": "Conference", "tone": "", "expected": "error"},
        
        # Cost modes
        {"category": "Technology", "event_type": "Conference", "tone": "Professional", "cost_mode": "economy", "expected": "success"},
        {"category": "Technology", "event_type": "Conference", "tone": "Professional", "cost_mode": "premium", "expected": "success"},
    ]
    
    results = []
    for i, case in enumerate(test_cases):
        logger.info(f"Running test case {i+1}/{len(test_cases)}")
        try:
            titles, logs = generate_titles(
                case.get("category", ""),
                case.get("event_type", ""),
                case.get("tone", ""),
                case.get("num_titles", 3),
                case.get("context"),
                case.get("cost_mode", "balanced")
            )
            
            if case["expected"] == "error" and not logs.get("errors"):
                results.append(f"FAIL: Test {i+1} should have failed but didn't")
            elif case["expected"] == "success" and logs.get("errors"):
                results.append(f"FAIL: Test {i+1} failed unexpectedly: {logs.get('errors')}")
            else:
                results.append(f"PASS: Test {i+1}")
                
        except Exception as e:
            if case["expected"] == "error":
                results.append(f"PASS: Test {i+1} (expected error: {e})")
            else:
                results.append(f"FAIL: Test {i+1} unexpected error: {e}")
    
    return results 