import json
import os
import time
from dotenv import load_dotenv
from difflib import get_close_matches
import streamlit as st
from openai import OpenAI

load_dotenv()

def get_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key and 'st' in globals():
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except:
            pass
    return api_key

API_KEY = get_api_key()

if not API_KEY:
    if 'st' in globals():
        st.error("⚠️ OpenAI API key not found! Please add OPENAI_API_KEY to your Streamlit secrets.")
        st.stop()
    else:
        raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or add to Streamlit secrets.")

client = OpenAI(api_key=API_KEY)

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
    return max(len(text.split()), int(len(text) / 3.5))

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
    return errors, warnings

def generate_titles(category, event_type, tone, num_titles=5, context=None, cost_mode="balanced"):
    errors, warnings = validate_inputs(category, event_type, tone, num_titles, context)
    if errors:
        return [], {"errors": errors, "warnings": warnings}
    
    num_titles = max(1, min(int(num_titles), 5))
    diversity_instruction = "Each title must be unique, creative, and use different wording. Avoid repeating phrases or structures."
    if cost_mode == "economy":
        system_msg = f"Generate {num_titles} creative, unique {tone.lower()} event titles for {category} {event_type}. 3-6 words each, no colons. JSON format. {diversity_instruction}"
        user_msg = f"Create {num_titles} unique, creative titles for {category} {event_type} ({tone})"
        max_tokens = 12 * num_titles + 30  # Slightly higher for more creativity
        temperature = 0.85
    elif cost_mode == "premium":
        # More few-shot examples for diversity
        examples = get_title_examples(category, event_type, tone)
        example_block = "\n".join([
            "[\"Innovate Now Summit\", \"Future Leaders Forum\", \"Tech Vision Expo\"]",
            "[\"Business Growth Bootcamp\", \"Leadership Mastery Workshop\", \"Strategic Success Seminar\"]",
            "[\"Learning Revolution Conference\", \"Education Innovation Forum\", \"Teaching Excellence Expo\"]"
        ])
        context_str = f" Context: {context}" if context else ""
        system_msg = f"""Expert event marketer. Generate {num_titles} compelling {tone.lower()} titles for {category} {event_type}.
Requirements: 3-6 words, memorable, actionable. Each title must be unique and use different words or focus. Avoid repeating phrases or structures.
Format: JSON array
Diverse Example Sets:\n{example_block}{context_str}"""
        user_msg = f"Generate {num_titles} exceptional, unique titles for {category} {event_type} with {tone} tone{context_str}"
        max_tokens = 15 * num_titles + 50
        temperature = 0.85
    else:  # balanced
        examples = get_title_examples(category, event_type, tone)
        context_str = f" Focus: {context}" if context else ""
        system_msg = f"""Professional event title generator. Create {num_titles} {tone.lower()} titles for {category} {event_type}.
- Length: 3-6 words
- Style: {tone.lower()}, memorable
- Format: JSON array
- Each title must be unique and use different words or focus. Avoid repeating phrases or structures.
Examples: {examples[0]}, {examples[1]}{context_str}"""
        user_msg = f"Generate {num_titles} unique titles: {category} {event_type} ({tone}){context_str}"
        max_tokens = 12 * num_titles + 30
        temperature = 0.8
    start = time.time()
    def call_llm(system_msg, user_msg, max_tokens, temperature):
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
        return response.choices[0].message.content.strip()
    result = call_llm(system_msg, user_msg, max_tokens, temperature)
    cleaned = clean_json_output(result)
    titles = []
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            titles = [str(t).strip() for t in parsed if isinstance(t, str) and t.strip()]
            titles = [t for t in titles if 3 <= len(t.split()) <= 6]
    except Exception as e:
        lines = result.replace('[', '').replace(']', '').replace('"', '').split(',')
        for line in lines:
            clean = line.strip().strip('"').strip("'").strip('-').strip('1234567890.').strip()
            if clean and 3 <= len(clean.split()) <= 6 and clean not in titles:
                titles.append(clean)
                if len(titles) >= num_titles:
                    break
    # Post-process: ensure all titles are unique
    seen = set()
    unique_titles = []
    for t in titles:
        if t.lower() not in seen:
            unique_titles.append(t)
            seen.add(t.lower())
    titles = unique_titles[:num_titles]
    # If still not enough, retry once with higher randomness (economy mode only)
    if cost_mode == "economy" and len(titles) < num_titles:
        result2 = call_llm(system_msg, user_msg, max_tokens + 20, 0.95)
        cleaned2 = clean_json_output(result2)
        try:
            parsed2 = json.loads(cleaned2)
            if isinstance(parsed2, list):
                for t in parsed2:
                    t = str(t).strip()
                    if t and 3 <= len(t.split()) <= 6 and t.lower() not in seen:
                        titles.append(t)
                        seen.add(t.lower())
                        if len(titles) >= num_titles:
                            break
        except Exception as e:
            pass
    titles = titles[:num_titles]
    # If still not enough, fill with generic but relevant titles
    fallback_used = False
    i = 1
    while len(titles) < num_titles:
        filler = f"{category} {event_type} Title {i}"
        if filler.lower() not in seen:
            titles.append(filler)
            seen.add(filler.lower())
            fallback_used = True
        i += 1
    warning = None
    if fallback_used:
        warning = f"Some titles are generic due to LLM output limits in {cost_mode} mode. Try balanced or premium for more creative results."
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
        "Efficiency score": round(efficiency_score, 2),
        "Model": "gpt-3.5-turbo",
        "System prompt": system_msg,
        "User prompt": user_msg
    }
    if warning:
        logs["Warnings"] = warning
    return titles, logs

def generate_description(title, category, event_type, tone, context=None, max_chars=2000, cost_mode="balanced"):
    max_chars = max(100, min(int(max_chars), 2000))
    
    end_instruction = "Do not stop until you reach the character limit. End with a strong call-to-action. Avoid repeating phrases. Use varied sentence structures."
    if cost_mode == "economy":
        system_msg = f"Write compelling {tone.lower()} description for '{title}' - {category} {event_type}. EXACTLY {max_chars} characters. Include benefits and call-to-action. Use all available space. {end_instruction}"
        user_msg = f"Description for: {title} ({category} {event_type}, {tone}) (MUST be {max_chars} characters)"
        max_tokens = int(max_chars/2.8) + 50
        temperature = 0.7
    elif cost_mode == "premium":
        context_str = f" Focus: {context}" if context else ""
        system_msg = f"""Expert copywriter. Write compelling {max_chars}-character description for '{title}' - {tone.lower()} {event_type} in {category}.
Structure: Hook → Problem → Solution → Benefits → CTA
Tone: {tone.lower()}, persuasive, action-oriented
TARGET: Use the full {max_chars} characters available. Do not stop early. Fill all space. {end_instruction}{context_str}"""
        user_msg = f"Write description for '{title}' ({category} {event_type}, {tone}). MUST be as close as possible to {max_chars} characters."
        max_tokens = int(max_chars/2.5) + 100
        temperature = 0.75
    else:  # balanced
        context_str = f" Focus: {context}" if context else ""
        system_msg = f"""Professional copywriter. Create engaging {tone.lower()} description for '{title}' - {category} {event_type}.
Length: EXACTLY {max_chars} characters (use all available space, do not stop early)
Include: value proposition, benefits, call-to-action
Style: {tone.lower()}, compelling{context_str}
{end_instruction}"""
        user_msg = f"Write description: '{title}' ({category} {event_type}, {tone}). Target {max_chars} chars. Use all available space." + (f" {context_str}" if context_str else "")
        max_tokens = int(max_chars/2.6) + 75
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
        
        # If description is significantly shorter than requested, try to extend it
        if len(description) < int(0.75 * max_chars) and cost_mode != "economy":
            remaining_chars = max_chars - len(description)
            
            extend_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are extending an event description. Add {remaining_chars} more characters to make it more detailed and compelling."},
                    {"role": "user", "content": f"Current description: {description}\n\nExpand this by adding more details, benefits, or call-to-action to reach closer to {max_chars} total characters."}
                ],
                max_tokens=int(remaining_chars/2.5) + 30,
                temperature=temperature
            )
            
            extension = extend_response.choices[0].message.content.strip()
            if extension and not extension.lower().startswith(description.lower()[:20]):
                description = description + " " + extension
        
    except Exception as e:
        return "", {"error": str(e)}
    
    end = time.time()
    
    prompt_tokens = count_tokens(system_msg) + count_tokens(user_msg)
    completion_tokens = count_tokens(description)
    total_tokens = prompt_tokens + completion_tokens
    cost = estimate_cost(prompt_tokens, completion_tokens)
    too_short = len(description) < int(0.6 * max_chars)
    
    char_efficiency = len(description) / cost if cost > 0 else 0
    
    # Post-process: trim to last period if truncation occurs
    if len(description) > max_chars:
        description = description[:max_chars]
        if '.' in description:
            description = description[:description.rfind('.')+1]
    
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
        "Shorter than requested": too_short,
        # For regeneration
        "category": category,
        "event_type": event_type,
        "tone": tone,
        "context": context,
        "max_chars": max_chars,
        "model": "gpt-3.5-turbo",
        "system_prompt": system_msg,
        "user_prompt": user_msg
    }
    
    return description, logs

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