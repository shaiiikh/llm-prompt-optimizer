import json
import os
import time
import hashlib
import pickle
from datetime import datetime, timedelta
from dotenv import load_dotenv
from difflib import get_close_matches
import streamlit as st
from openai import OpenAI
import random

load_dotenv()

class SmartCache:
    def __init__(self, cache_dir="cache", ttl_hours=48):
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        self.memory_cache = {}
        self.max_memory_items = 100
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_key(self, *args, **kwargs):
        content = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def get(self, key):
        if key in self.memory_cache:
            data = self.memory_cache[key]
            if datetime.now() - data['timestamp'] < self.ttl:
                return data['content']
            else:
                del self.memory_cache[key]
        
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                if datetime.now() - data['timestamp'] < self.ttl:
                    if len(self.memory_cache) < self.max_memory_items:
                        self.memory_cache[key] = data
                    return data['content']
                else:
                    os.remove(cache_file)
            except:
                pass
        return None
    
    def set(self, key, content):
        data = {
            'content': content,
            'timestamp': datetime.now()
        }
        
        if len(self.memory_cache) >= self.max_memory_items:
            oldest_key = min(self.memory_cache.keys(), key=lambda k: self.memory_cache[k]['timestamp'])
            del self.memory_cache[oldest_key]
        
        self.memory_cache[key] = data
        
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except:
            pass

class PromptOptimizer:
    @staticmethod
    def compress_prompt(prompt, target_reduction=0.3):
        lines = prompt.split('\n')
        essential_lines = []
        for line in lines:
            if any(keyword in line.upper() for keyword in ['CRITICAL', 'MUST', 'REQUIRED', 'ESSENTIAL']):
                essential_lines.append(line)
            elif len(line.strip()) > 10 and not line.strip().startswith('-'):
                essential_lines.append(line[:int(len(line) * (1 - target_reduction))])
        return '\n'.join(essential_lines)
    
    @staticmethod
    def optimize_for_cost(prompt, cost_mode):
        if cost_mode == "economy":
            compressed = PromptOptimizer.compress_prompt(prompt, 0.5)
            return compressed.replace("Please provide", "Provide").replace("You should", "").replace("It is important to", "").replace("Make sure to", "")
        elif cost_mode == "premium":
            return prompt
        else:
            return PromptOptimizer.compress_prompt(prompt, 0.25)

class BatchProcessor:
    @staticmethod
    def can_batch(requests):
        return len(requests) > 1 and all(req.get('model') == requests[0].get('model') for req in requests)
    
    @staticmethod
    def create_batch_prompt(requests):
        batch_prompt = "Generate the following items in JSON format:\n"
        for i, req in enumerate(requests):
            batch_prompt += f"{i+1}. {req['type']}: {req['prompt']}\n"
        batch_prompt += "\nReturn as JSON array with 'type', 'content', and 'index' fields."
        return batch_prompt

class PerformanceAnalytics:
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'total_cost': 0.0,
            'total_tokens': 0,
            'avg_response_time': 0.0,
            'error_rate': 0.0
        }
    
    def record_request(self, cost, tokens, response_time, from_cache=False, error=False):
        self.metrics['total_requests'] += 1
        if from_cache:
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['total_cost'] += cost
            self.metrics['total_tokens'] += tokens
        
        current_avg = self.metrics['avg_response_time']
        self.metrics['avg_response_time'] = (current_avg * (self.metrics['total_requests'] - 1) + response_time) / self.metrics['total_requests']
        
        if error:
            self.metrics['error_rate'] = (self.metrics['error_rate'] * (self.metrics['total_requests'] - 1) + 1) / self.metrics['total_requests']
    
    def get_efficiency_score(self):
        if self.metrics['total_requests'] == 0:
            return 0
        
        cache_efficiency = min(self.metrics['cache_hits'] / self.metrics['total_requests'], 1.0)
        
        avg_cost_per_request = self.metrics['total_cost'] / self.metrics['total_requests'] if self.metrics['total_requests'] > 0 else 0
        cost_efficiency = max(0, 1 - min(avg_cost_per_request / 0.005, 1))
        
        speed_efficiency = max(0, 1 - min(self.metrics['avg_response_time'] / 15, 1))
        
        error_efficiency = 1 - self.metrics['error_rate']
        
        token_efficiency = max(0, 1 - min((self.metrics['total_tokens'] / self.metrics['total_requests']) / 2000, 1)) if self.metrics['total_requests'] > 0 else 0
        
        weights = [0.25, 0.20, 0.25, 0.20, 0.10]
        components = [cache_efficiency, cost_efficiency, speed_efficiency, error_efficiency, token_efficiency]
        
        return sum(w * c for w, c in zip(weights, components)) * 100

cache = SmartCache()
analytics = PerformanceAnalytics()

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
        st.error("OpenAI API key not found! Please add OPENAI_API_KEY to your Streamlit secrets.")
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

def estimate_cost(prompt_tokens, completion_tokens, model="gpt-3.5-turbo"):
    costs = {
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "dall-e-3": {"image": 0.04}
    }
    
    if model in costs and "input" in costs[model]:
        input_cost = costs[model]["input"] * (prompt_tokens / 1000)
        output_cost = costs[model]["output"] * (completion_tokens / 1000)
        return input_cost + output_cost
    return 0.02

def count_tokens(text):
    return max(len(text.split()), int(len(text) / 3.5))

def fuzzy_correct(user_input, valid_options):
    matches = get_close_matches(user_input, valid_options, n=1, cutoff=0.75)
    if matches:
        return matches[0]
    return user_input

def smart_api_call(system_msg, user_msg, max_tokens, temperature, model="gpt-3.5-turbo", cost_mode="balanced"):
    start_time = time.time()
    
    optimized_system = PromptOptimizer.optimize_for_cost(system_msg, cost_mode)
    optimized_user = PromptOptimizer.optimize_for_cost(user_msg, cost_mode)
    
    cache_key = cache._get_cache_key(optimized_system, optimized_user, max_tokens, temperature, model)
    cached_result = cache.get(cache_key)
    
    if cached_result:
        analytics.record_request(0, 0, time.time() - start_time, from_cache=True)
        return cached_result
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": optimized_system},
                    {"role": "user", "content": optimized_user}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                frequency_penalty=0.6,
                presence_penalty=0.4
            )
            
            result = response.choices[0].message.content.strip()
            cache.set(cache_key, result)
            
            prompt_tokens = count_tokens(optimized_system + optimized_user)
            completion_tokens = count_tokens(result)
            cost = estimate_cost(prompt_tokens, completion_tokens, model)
            
            analytics.record_request(cost, prompt_tokens + completion_tokens, time.time() - start_time)
            return result
            
        except Exception as e:
            if attempt == max_retries - 1:
                analytics.record_request(0, 0, time.time() - start_time, error=True)
                raise e
            time.sleep(2 ** attempt)

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
    diversity_instruction = "Each title must be unique, creative, and use different wording. Avoid repeating phrases or structures. No emojis or decorative symbols."
    
    if cost_mode == "economy":
        context_str = f" Focus: {context}" if context else ""
        system_msg = f"Generate {num_titles} creative, unique {tone.lower()} event titles for {category} {event_type}. 3-6 words each, no colons. JSON format. {diversity_instruction}{context_str}"
        user_msg = f"Create {num_titles} unique, creative titles for {category} {event_type} ({tone}){context_str}"
        max_tokens = 15 * num_titles + 40
        temperature = 0.85
    elif cost_mode == "premium":
        examples = get_title_examples(category, event_type, tone)
        example_block = "\n".join([
            "[\"Innovate Now Summit\", \"Future Leaders Forum\", \"Tech Vision Expo\"]",
            "[\"Business Growth Bootcamp\", \"Leadership Mastery Workshop\", \"Strategic Success Seminar\"]",
            "[\"Learning Revolution Conference\", \"Education Innovation Forum\", \"Teaching Excellence Expo\"]"
        ])
        context_str = f" Context: {context}" if context else ""
        system_msg = f"""Expert event marketer. Generate EXACTLY {num_titles} compelling {tone.lower()} titles for {category} {event_type}.

CRITICAL REQUIREMENTS:
- Generate EXACTLY {num_titles} titles, no more, no less
- Each title must be 3-6 words long
- Each title must be unique and creative
- Use different words, phrases, and focus areas for each title
- Format as a clean JSON array: ["Title 1", "Title 2", "Title 3"]
- NO explanations, NO extra text, just the JSON array

Examples of diverse titles:
{example_block}

Style: {tone.lower()}, memorable, actionable{context_str}"""
        user_msg = f"Generate EXACTLY {num_titles} exceptional, unique titles for {category} {event_type} with {tone} tone. Return only a JSON array.{context_str}"
        max_tokens = 20 * num_titles + 60
        temperature = 0.9
    else:
        examples = get_title_examples(category, event_type, tone)
        context_str = f" Focus: {context}" if context else ""
        system_msg = f"""Professional event title generator. Create EXACTLY {num_titles} {tone.lower()} titles for {category} {event_type}.

REQUIREMENTS:
- Generate EXACTLY {num_titles} titles
- Length: 3-6 words each
- Style: {tone.lower()}, memorable
- Format: JSON array only
- Each title must be unique and use different words or focus
- Avoid repeating phrases or structures

Examples: {examples[0]}, {examples[1]}{context_str}"""
        user_msg = f"Generate EXACTLY {num_titles} unique titles: {category} {event_type} ({tone}). Return JSON array only.{context_str}"
        max_tokens = 18 * num_titles + 50
        temperature = 0.85
    
    start = time.time()
    
    result = smart_api_call(system_msg, user_msg, max_tokens, temperature, cost_mode=cost_mode)
    cleaned = clean_json_output(result)
    titles = []
    parsing_error = None
    
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            titles = [str(t).strip() for t in parsed if isinstance(t, str) and t.strip()]
            titles = [t for t in titles if 3 <= len(t.split()) <= 6]
        else:
            parsing_error = "JSON is not a list"
    except Exception as e:
        parsing_error = str(e)
        lines = result.replace('[', '').replace(']', '').replace('"', '').split(',')
        for line in lines:
            clean = line.strip().strip('"').strip("'").strip('-').strip('1234567890.').strip()
            if clean and 3 <= len(clean.split()) <= 6 and clean not in titles:
                titles.append(clean)
                if len(titles) >= num_titles:
                    break
    
    seen = set()
    unique_titles = []
    for t in titles:
        if t.lower() not in seen:
            unique_titles.append(t)
            seen.add(t.lower())
    titles = unique_titles[:num_titles]
    
    retry_count = 0
    max_retries = 2 if cost_mode == "premium" else 1
    
    while len(titles) < num_titles and retry_count < max_retries:
        retry_count += 1
        needed = num_titles - len(titles)
        
        retry_system = system_msg.replace(f"EXACTLY {num_titles}", f"EXACTLY {needed} additional")
        retry_user = f"Generate {needed} more unique titles for {category} {event_type} ({tone}). Avoid these existing titles: {', '.join(titles)}. Return JSON array only."
        
        result2 = smart_api_call(retry_system, retry_user, max_tokens + 20, temperature + 0.1, cost_mode=cost_mode)
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
            lines = result2.replace('[', '').replace(']', '').replace('"', '').split(',')
            for line in lines:
                clean = line.strip().strip('"').strip("'").strip('-').strip('1234567890.').strip()
                if clean and 3 <= len(clean.split()) <= 6 and clean.lower() not in seen:
                    titles.append(clean)
                    seen.add(clean.lower())
                    if len(titles) >= num_titles:
                        break
    
    titles = titles[:num_titles]
    
    fallback_used = False
    creative_fallbacks = [
        f"{category} Excellence Summit",
        f"Future of {category}",
        f"{tone} {event_type} Experience",
        f"Next-Gen {category} Forum",
        f"Advanced {event_type} Series",
        f"{category} Innovation Hub",
        f"Premier {event_type} Event",
        f"{tone} {category} Gathering",
        f"Professional {event_type} Network",
        f"Elite {category} Conference"
    ]
    
    fallback_index = 0
    while len(titles) < num_titles and fallback_index < len(creative_fallbacks):
        candidate = creative_fallbacks[fallback_index]
        if candidate.lower() not in seen and 3 <= len(candidate.split()) <= 6:
            titles.append(candidate)
            seen.add(candidate.lower())
            fallback_used = True
        fallback_index += 1
    
    i = 1
    while len(titles) < num_titles:
        filler = f"{category} {event_type} {i}"
        if filler.lower() not in seen:
            titles.append(filler)
            seen.add(filler.lower())
            fallback_used = True
        i += 1
    
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
        "User prompt": user_msg,
        "Retry count": retry_count,
        "Titles requested": num_titles,
        "Titles generated": len(titles),
        "Cache hit": analytics.metrics['cache_hits'] > 0,
        "Overall efficiency": f"{analytics.get_efficiency_score():.1f}%"
    }
    
    warnings = []
    if fallback_used:
        warnings.append(f"Some titles use creative fallbacks due to LLM output limits in {cost_mode} mode.")
    if parsing_error:
        warnings.append(f"JSON parsing issue: {parsing_error}")
    if retry_count > 0:
        warnings.append(f"Required {retry_count} retries to generate sufficient titles.")
    
    if warnings:
        logs["Warnings"] = "; ".join(warnings)
    
    return titles, logs

def generate_description(title, category, event_type, tone, context=None, max_chars=5000, cost_mode="balanced"):
    max_chars = max(100, min(int(max_chars), 5000))
    
    end_instruction = "Write in flowing paragraphs without bullet points or numbered lists. Use natural transitions between ideas. End with a strong call-to-action. No emojis or decorative symbols."
    if cost_mode == "economy":
        context_str = f" Focus: {context}" if context else ""
        system_msg = f"Write compelling {tone.lower()} description for '{title}' - {category} {event_type}. EXACTLY {max_chars} characters. Include benefits and call-to-action. Use all available space. {end_instruction}{context_str}"
        user_msg = f"Description for: {title} ({category} {event_type}, {tone}) (MUST be {max_chars} characters){context_str}"
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
    else:
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
        description = smart_api_call(system_msg, user_msg, max_tokens, temperature, cost_mode=cost_mode)
        
        if len(description) < int(0.75 * max_chars) and cost_mode != "economy":
            remaining_chars = max_chars - len(description)
            extend_system = f"You are extending an event description. Add {remaining_chars} more characters to make it more detailed and compelling."
            extend_user = f"Current description: {description}\n\nExpand this by adding more details, benefits, or call-to-action to reach closer to {max_chars} total characters."
            
            extension = smart_api_call(extend_system, extend_user, int(remaining_chars/2.5) + 30, temperature, cost_mode=cost_mode)
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

def generate_faqs(title, description, category, event_type, tone, context=None, cost_mode="balanced"):
    event_specific_faqs = {
        "Conference": [
            {"q": "What is the dress code for the conference?", "a": "Business casual attire is recommended for all conference sessions and networking events."},
            {"q": "Will presentations be available after the conference?", "a": "Yes, all presentation slides and session recordings will be shared with attendees within one week after the event."},
            {"q": "Is there a mobile app for the conference?", "a": "Yes, our conference app will be available for download one week before the event with the full schedule, speaker profiles, and networking features."}
        ],
        "Workshop": [
            {"q": "Do I need to bring my own equipment?", "a": "All necessary equipment will be provided. Please bring only a notepad and pen for taking notes."},
            {"q": "What is the participant to instructor ratio?", "a": "We maintain a 15:1 participant to instructor ratio to ensure personalized attention."},
            {"q": "Will there be hands-on activities?", "a": "Yes, this workshop is designed to be interactive with at least 60% of the time dedicated to hands-on activities."}
        ],
        "Festival": [
            {"q": "Are there food and beverages available at the festival?", "a": "Yes, a variety of food vendors and beverage stations will be available throughout the festival grounds."},
            {"q": "Can I bring my own food or drinks?", "a": "Outside food and beverages are not permitted, but exceptions are made for medical requirements and baby food."},
            {"q": "Is the festival family-friendly?", "a": "Yes, we welcome attendees of all ages with dedicated areas and activities for children."}
        ],
        "Seminar": [
            {"q": "Will there be Q&A sessions?", "a": "Yes, each presentation will be followed by a 15-minute Q&A session with the speaker."},
            {"q": "Are the seminar materials included in the registration fee?", "a": "Yes, all seminar materials, including handouts and digital resources, are included in your registration."},
            {"q": "Will I receive a certificate of attendance?", "a": "Yes, certificates of attendance will be provided to all participants at the conclusion of the seminar."}
        ]
    }
    
    refund_policies = {
        "Conference": "Full refunds available up to 30 days before the event. 50% refund available between 30 and 14 days before the event. No refunds within 14 days of the event. Ticket transfers are permitted at any time.",
        "Workshop": "Full refunds available up to 14 days before the workshop. 50% refund available between 14 and 7 days before. No refunds within 7 days of the workshop. You may transfer your registration to another person at no cost.",
        "Festival": "Full refunds available up to 60 days before the festival. 75% refund up to 30 days before, 50% refund up to 14 days before. No refunds within 14 days. Ticket transfers allowed with a $15 processing fee.",
        "Seminar": "Full refunds available up to 14 days before the seminar. 50% refund available between 14 and 7 days before. No refunds within 7 days of the seminar. Ticket transfers are permitted at any time."
    }
    
    default_policy = "Full refunds available up to 14 days before the event. 50% refund available between 14 and 7 days before. No refunds within 7 days of the event. Ticket transfers are permitted at any time with written notice."
    
    few_shot = "Example FAQs:\n"
    
    if event_type in event_specific_faqs:
        for faq in event_specific_faqs[event_type][:2]:
            few_shot += f"Q: {faq['q']}\nA: {faq['a']}\n"
    
    few_shot += (
        "Q: What is the dress code for the event?\nA: The dress code is business casual.\n"
        "Q: Will meals be provided?\nA: Yes, lunch and refreshments will be served.\n"
        "Q: Can I transfer my ticket to someone else?\nA: Yes, please contact support to transfer your ticket.\n"
        "Q: Is parking available at the venue?\nA: Yes, free parking is available for all attendees.\n"
        "Q: Will the sessions be recorded?\nA: Yes, recordings will be shared after the event.\n"
        "---\n"
        "Example Refund Policy:\n"
    )
    
    if event_type in refund_policies:
        few_shot += refund_policies[event_type] + "\n"
    else:
        few_shot += default_policy + "\n"
    
    system_prompt = (
        f"You are an expert event manager specializing in {category} {event_type}s. "
        f"Your task is to create professional, clear, and helpful FAQs and a fair refund policy "
        f"that matches the {tone.lower()} tone of this {event_type}."
    )
    
    user_prompt = (
        f"Based on the following event details, generate at least 5 relevant, clear, and professional FAQs with detailed answers.\n"
        f"Event Title: {title}\n"
        f"Description: {description}\n"
        f"Category: {category}\n"
        f"Event Type: {event_type}\n"
        f"Tone: {tone}\n"
        f"{f'Context: {context}' if context else ''}\n\n"
        f"Requirements:\n"
        f"1. Create at least 5 FAQs that directly address likely questions about this specific event\n"
        f"2. Make answers informative, helpful, and in a {tone.lower()} tone\n"
        f"3. Focus on practical questions attendees would actually ask\n"
        f"4. Include questions about logistics, content, requirements, and benefits\n"
        f"5. Use professional language without emojis or decorative symbols\n\n"
        f"Example FAQ format:\n"
        f"Q: What is the dress code for the event?\nA: Business casual attire is recommended.\n"
        f"Q: Will meals be provided?\nA: Yes, lunch and refreshments will be served.\n\n"
        f"Now generate FAQs for this event. Format:\nQ: ...\nA: ...\n"
    )
    
    start = time.time()
    try:
        output = smart_api_call(system_prompt, user_prompt, 1200, 0.7, cost_mode=cost_mode)
    except Exception as e:
        return [], "", {"error": str(e)}
    end = time.time()
    
    faqs = []
    faqs_part = output
    
    current_question = ""
    current_answer = ""
    
    for line in faqs_part.splitlines():
        line = line.strip()
        if not line or line == "FAQs:":
            continue
            
        if line.startswith("Q:") or line.startswith("Q.") or line.startswith("Question:"):
            if current_question and current_answer:
                faqs.append({"question": current_question, "answer": current_answer})
            
            current_question = line.split(":", 1)[1].strip() if ":" in line else line[2:].strip()
            current_answer = ""
        elif line.startswith("A:") or line.startswith("A.") or line.startswith("Answer:"):
            current_answer = line.split(":", 1)[1].strip() if ":" in line else line[2:].strip()
        elif current_question and not current_answer:
            current_answer = line
        elif current_answer:
            current_answer += " " + line
    
    if current_question and current_answer:
        faqs.append({"question": current_question, "answer": current_answer})
    
    if len(faqs) < 5 and event_type in event_specific_faqs:
        for faq in event_specific_faqs[event_type]:
            if len(faqs) >= 5:
                break
            if not any(f["question"].lower() == faq["q"].lower() for f in faqs):
                faqs.append({"question": faq["q"], "answer": faq["a"]})
    
    prompt_tokens = count_tokens(system_prompt) + count_tokens(user_prompt)
    completion_tokens = count_tokens(output)
    total_tokens = prompt_tokens + completion_tokens
    cost = estimate_cost(prompt_tokens, completion_tokens)
    logs = {
        "Prompt tokens": prompt_tokens,
        "Completion tokens": completion_tokens,
        "Total tokens": total_tokens,
        "Time taken (s)": round(end - start, 2),
        "Estimated cost ($)": f"${cost:.5f}",
        "Model": "gpt-3.5-turbo",
        "Prompt": user_prompt,
        "System prompt": system_prompt,
        "Cost mode": cost_mode
    }
    return faqs, logs

def generate_refund_policy(title, description, category, event_type, tone, context=None, cost_mode="balanced"):
    refund_policies = {
        "Conference": "Full refunds available up to 30 days before the event. 50% refund available between 30 and 14 days before the event. No refunds within 14 days of the event. Ticket transfers are permitted at any time.",
        "Workshop": "Full refunds available up to 14 days before the workshop. 50% refund available between 14 and 7 days before. No refunds within 7 days of the workshop. You may transfer your registration to another person at no cost.",
        "Festival": "Full refunds available up to 60 days before the festival. 75% refund up to 30 days before, 50% refund up to 14 days before. No refunds within 14 days. Ticket transfers allowed with a $15 processing fee.",
        "Seminar": "Full refunds available up to 14 days before the seminar. 50% refund available between 14 and 7 days before. No refunds within 7 days of the seminar. Ticket transfers are permitted at any time.",
        "Webinar": "Full refunds available up to 7 days before the webinar. 50% refund available between 7 and 3 days before. No refunds within 3 days of the webinar. Registration transfers are permitted at any time.",
        "Exhibition": "Full refunds available up to 21 days before the exhibition. 50% refund available between 21 and 10 days before. No refunds within 10 days. Ticket transfers permitted with notification.",
        "Meetup": "Full refunds available up to 7 days before the meetup. 50% refund available between 7 and 3 days before. No refunds within 3 days. Registration transfers are always permitted.",
        "Gala": "Full refunds available up to 45 days before the gala. 75% refund up to 30 days before, 50% refund up to 14 days before. No refunds within 14 days. Ticket transfers allowed with advance notice."
    }
    
    default_policy = "Full refunds available up to 14 days before the event. 50% refund available between 14 and 7 days before. No refunds within 7 days of the event. Ticket transfers are permitted at any time with written notice."
    
    system_prompt = (
        f"You are an expert event manager and legal advisor specializing in creating fair, clear, and professional refund policies. "
        f"Create a comprehensive refund policy that is appropriate for a {category} {event_type} with a {tone.lower()} tone. "
        f"The policy should be clear, fair to both organizers and attendees, and legally sound."
    )
    
    user_prompt = (
        f"Create a professional, clear, and fair refund policy for the following event:\n"
        f"Event Title: {title}\n"
        f"Description: {description}\n"
        f"Category: {category}\n"
        f"Event Type: {event_type}\n"
        f"Tone: {tone}\n"
        f"{f'Context: {context}' if context else ''}\n\n"
        f"Requirements:\n"
        f"1. Create a clear, professional refund policy appropriate for this event type\n"
        f"2. Include specific timeframes for different refund percentages\n"
        f"3. Address ticket transfers and cancellation procedures\n"
        f"4. Use a {tone.lower()} tone while maintaining legal clarity\n"
        f"5. Consider the event category and type when setting terms\n"
        f"6. Use professional language without emojis or decorative symbols\n\n"
        f"Example policy structure:\n"
        f"Full refunds available up to X days before the event. Partial refunds available between X and Y days. No refunds within Y days. Transfer policies and contact information.\n\n"
        f"Generate a comprehensive refund policy for this {event_type}:"
    )
    
    start = time.time()
    try:
        refund_policy = smart_api_call(system_prompt, user_prompt, 600, 0.7, cost_mode=cost_mode)
    except Exception as e:
        refund_policy = refund_policies.get(event_type, default_policy)
    
    end = time.time()
    
    if len(refund_policy) < 100:
        refund_policy = refund_policies.get(event_type, default_policy)
    
    prompt_tokens = count_tokens(system_prompt) + count_tokens(user_prompt)
    completion_tokens = count_tokens(refund_policy)
    total_tokens = prompt_tokens + completion_tokens
    cost = estimate_cost(prompt_tokens, completion_tokens)
    
    logs = {
        "Prompt tokens": prompt_tokens,
        "Completion tokens": completion_tokens,
        "Total tokens": total_tokens,
        "Time taken (s)": round(end - start, 2),
        "Estimated cost ($)": f"${cost:.5f}",
        "Model": "gpt-3.5-turbo",
        "Prompt": user_prompt,
        "System prompt": system_prompt,
        "Cost mode": cost_mode
    }
    
    return refund_policy, logs

def get_flyer_examples(category, event_type, tone):
    examples = [
        {"title": "Tech Leadership Summit", "description": "A premier gathering for technology leaders to explore innovation and future trends.", "category": "Technology", "event_type": "Conference", "tone": "Professional", "style": "Photorealistic modern design, sleek blue and white gradient, 3D tech elements, crystal clear bold title, professional lighting, high-contrast readable text"},
        {"title": "Art & Culture Fest", "description": "A vibrant celebration of art, music, and culture for all ages.", "category": "Arts & Culture", "event_type": "Festival", "tone": "Creative", "style": "Realistic artistic textures, vibrant color palette, professional photography style, bold readable typography, creative composition with clear text hierarchy"},
        {"title": "Business Growth Workshop", "description": "Unlock new strategies for business expansion and leadership.", "category": "Business", "event_type": "Workshop", "tone": "Professional", "style": "Corporate photorealistic design, professional blue and gray tones, 3D upward arrows, crystal clear title text, sophisticated layout, high-end business aesthetic"},
        {"title": "Health & Wellness Expo", "description": "Discover the latest in health, fitness, and wellness trends.", "category": "Health", "event_type": "Exhibition", "tone": "Friendly", "style": "Fresh photorealistic design, natural green and white palette, realistic wellness imagery, clear readable fonts, professional healthcare aesthetic"},
        {"title": "Kids Science Fair", "description": "An interactive science fair for children and families.", "category": "Education", "event_type": "Exhibition", "tone": "Playful", "style": "Bright photorealistic design, playful yet clear typography, educational elements, child-friendly but professional quality"},
        {"title": "Luxury Gala Night", "description": "An exclusive evening gala for charity and networking.", "category": "Business", "event_type": "Gala", "tone": "Premium", "style": "Ultra-premium photorealistic design, elegant gold and black palette, luxury textures, sophisticated typography, high-end event aesthetic"},
        {"title": "Startup Pitch Meetup", "description": "Pitch your startup to investors and network with founders.", "category": "Business", "event_type": "Meetup", "tone": "Innovative", "style": "Modern photorealistic design, innovative blue and orange palette, tech-forward elements, clear professional typography, startup-friendly aesthetic"},
        {"title": "Sports Fan Fest", "description": "A festival for sports fans with games and food.", "category": "Sports", "event_type": "Festival", "tone": "Casual", "style": "Dynamic photorealistic design, energetic team colors, sports photography style, bold readable text, festival atmosphere with professional quality"},
    ]
    filtered = [ex for ex in examples if ex["category"] == category and ex["event_type"] == event_type and ex["tone"] == tone]
    if filtered:
        return filtered[0]
    for ex in examples:
        if ex["category"] == category and ex["event_type"] == event_type:
            return ex
    for ex in examples:
        if ex["category"] == category:
            return ex
    return random.choice(examples)

def get_dynamic_style(category, event_type, tone):
    if category == "Business" and event_type == "Gala":
        return "Ultra-premium photorealistic design, elegant gold and black palette, luxury textures, crystal clear sophisticated typography, high-end event aesthetic"
    if category == "Education" and tone == "Playful":
        return "Bright photorealistic design, playful yet readable typography, educational elements, child-friendly but professional quality"
    if category == "Technology":
        return "Photorealistic futuristic design, sleek blue tones, 3D digital elements, modern clean layout, crystal clear bold text, tech-forward aesthetic"
    if category == "Sports":
        return "Dynamic photorealistic design, energetic team colors, sports photography style, bold readable typography, athletic festival atmosphere"
    if category == "Arts & Culture":
        return "Realistic artistic textures, vibrant creative palette, professional photography style, clear typography hierarchy, cultural sophistication"
    if tone == "Premium":
        return "Ultra-premium photorealistic design, luxury gold accents, high-end textures, sophisticated readable typography, elite quality aesthetic"
    if tone == "Friendly":
        return "Fresh photorealistic design, natural green and white palette, approachable clean layout, clear readable fonts, welcoming professional quality"
    return "Modern photorealistic design, professional creative elements, vibrant high-quality palette, crystal clear typography, visually engaging premium aesthetic"

def extract_event_details(context):
    """Extract specific event details from context"""
    import re
    
    details = {
        'time': None,
        'date': None,
        'location': None,
        'speakers': None,
        'online_offline': None,
        'timezone': None,
        'registration': None,
        'price': None
    }
    
    if not context:
        return details
    
    context_lower = context.lower()
    
    time_pattern = r'\b(\d{1,2}:\d{2}\s?(?:am|pm)|\d{1,2}\s?(?:am|pm)|\d{1,2}:\d{2})\b'
    time_match = re.search(time_pattern, context_lower)
    if time_match:
        details['time'] = time_match.group(1)
    
    if any(word in context_lower for word in ['online', 'virtual', 'zoom', 'webinar', 'remote', 'digital', 'streaming', 'livestream']):
        details['online_offline'] = 'online'
    elif any(word in context_lower for word in ['onsite', 'venue', 'hall', 'center', 'hotel', 'location', 'address', 'auditorium', 'conference center', 'convention', 'in-person', 'physical']):
        details['online_offline'] = 'offline'
    
    timezone_pattern = r'\b(pst|est|gmt|utc|pakistan time|pkt|ist|cet|cst|mst|pdt|edt)\b'
    tz_match = re.search(timezone_pattern, context_lower)
    if tz_match:
        tz = tz_match.group(1)
        details['timezone'] = tz.upper() if tz != 'pakistan time' else 'PKT'
    
    name_pattern = r'\b(?:speaker|presenter|host|keynote|guest|featuring|with)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:\s+(?:at|in|on|will|is|presenter|speaker)|\b)'
    name_match = re.search(name_pattern, context, re.IGNORECASE)
    if name_match:
        details['speakers'] = name_match.group(1).strip()
    else:
        capitalized_names = re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', context)
        if capitalized_names:
            clean_names = []
            for name in capitalized_names:
                if not any(word in name.lower() for word in ['team', 'conference', 'meeting', 'event', 'summit', 'pakistan', 'cricket']):
                    clean_names.append(name)
            if clean_names:
                details['speakers'] = clean_names[0]
    
    date_pattern = r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|\b(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}(?:st|nd|rd|th)?)\b'
    date_match = re.search(date_pattern, context_lower)
    if date_match:
        details['date'] = date_match.group(1)
    
    city_pattern = r'\b(?:in|at|location|venue)\s+([A-Z][a-z]+)(?:\s+(?:on|at|during|for)|\b)'
    city_match = re.search(city_pattern, context, re.IGNORECASE)
    if city_match:
        details['location'] = city_match.group(1)
    else:
        major_cities = ['karachi', 'lahore', 'islamabad', 'dubai', 'mumbai', 'delhi', 'london', 'new york', 'singapore', 'tokyo', 'paris', 'berlin', 'sydney', 'toronto', 'chicago']
        for city in major_cities:
            if city in context_lower:
                details['location'] = city.title()
                break
    
    return details

def generate_flyer_image(title, description, category, event_type, tone, context=None, cost_mode="balanced", image_size="1024x1024"):
    example = get_flyer_examples(category, event_type, tone)
    event_details = extract_event_details(context)
    
    flyer_specific_requirements = (
        "FLYER DESIGN SPECIFICATIONS:\n"
        "- FLYERS are typically PORTRAIT orientation (vertical) for print and handheld distribution\n"
        "- Include ALL essential event information: title, date, time, location, speakers\n"
        "- Use HIERARCHICAL text layout: Title (largest) → Key details → Description\n"
        "- Perfect for: detailed event information, speaker names, schedules, contact details\n"
        "- Include clear sections for: WHO, WHAT, WHEN, WHERE information\n"
        "- Add subtle design elements that don't interfere with text readability\n"
    )
    
    text_optimization = (
        "CRITICAL TEXT REQUIREMENTS:\n"
        "- TITLE: Use EXTRA LARGE, BOLD fonts (minimum 32pt equivalent)\n"
        "- EVENT DETAILS: Medium-large fonts (18-24pt equivalent) for date, time, location\n"
        "- SPEAKER NAMES: Prominent, readable fonts (16-20pt equivalent)\n"
        "- Ensure MAXIMUM CONTRAST between all text and background\n"
        "- Use SOLID COLOR text boxes or backgrounds for important information\n"
        "- NEVER place critical text over busy patterns or gradients\n"
        "- Use WHITE text on dark backgrounds or BLACK text on light backgrounds\n"
        "- All text must be PERFECTLY READABLE from 3 feet away\n"
    )
    
    event_info_integration = "CRITICAL: MANDATORY EVENT DETAILS - MUST BE DISPLAYED ON FLYER\n"
    event_info_integration += "DALL-E: YOU ARE REQUIRED TO INCLUDE ALL PROVIDED DETAILS ON THE FLYER\n\n"
    
    has_details = event_details['time'] or event_details['date'] or event_details['speakers'] or event_details['location'] or event_details['online_offline']
    
    if has_details:
        event_info_integration += "REQUIRED INFORMATION TO DISPLAY (NON-NEGOTIABLE):\n"
        if event_details['date']:
            event_info_integration += f"DATE: {event_details['date']} (MANDATORY - Use HUGE fonts, place directly below title)\n"
        if event_details['time']:
            event_info_integration += f"TIME: {event_details['time']} (MANDATORY - Extra large fonts, highly visible)\n"
        if event_details['timezone']:
            event_info_integration += f"TIMEZONE: {event_details['timezone']} (Display next to time)\n"
        if event_details['speakers']:
            event_info_integration += f"SPEAKER: {event_details['speakers']} (CRITICAL - Use MASSIVE fonts, second most prominent after title)\n"
        if event_details['location']:
            event_info_integration += f"LOCATION: {event_details['location']} (MANDATORY - Large fonts with location icon)\n"
        if event_details['online_offline']:
            event_info_integration += f"FORMAT: {event_details['online_offline'].upper()} EVENT (Show with appropriate icon)\n"
        
        event_info_integration += "\nABSOLUTE NON-NEGOTIABLE REQUIREMENTS:\n"
        event_info_integration += "EVERY detail listed above MUST appear on the flyer - NO EXCEPTIONS\n"
        event_info_integration += "Use font hierarchy: Title (largest) → Speaker (massive) → Date/Time/Location (large)\n"
        event_info_integration += "High contrast colors - white text on dark backgrounds or dark text on light\n"
        event_info_integration += "NO detail can be omitted, hidden, or made too small to read\n"
        event_info_integration += "If you don't include ALL these details prominently, the flyer is REJECTED\n"
    
    if context and not has_details:
        event_info_integration += f"CONTEXT TO EXTRACT AND DISPLAY:\n{context}\n"
        event_info_integration += "Parse this text and extract ANY event details (names, dates, times, locations)\n"
        event_info_integration += "Make ALL extracted information HIGHLY visible on the flyer\n"
    elif context:
        event_info_integration += f"\nADDITIONAL CONTEXT:\n{context}\n"
        event_info_integration += "Include relevant additional details from this context\n"
    
    realism_enhancement = (
        "REALISM AND QUALITY REQUIREMENTS:\n"
        "- Use PHOTOREALISTIC design elements and textures\n"
        "- Apply PROFESSIONAL lighting with realistic shadows\n"
        "- Create DEPTH with layered composition and 3D effects\n"
        "- Use HIGH-RESOLUTION quality appearance throughout\n"
        "- Apply REALISTIC gradients and professional color schemes\n"
        "- Include SUBTLE branding elements that enhance professionalism\n"
        "- Use MARKETING-AGENCY quality design standards\n"
        "- Ensure PRINT-READY quality even for digital distribution\n"
    )
    
    negative_prompt = (
        "STRICTLY AVOID: Blurry or unreadable text, small fonts, low contrast text, "
        "text over busy backgrounds, pixelated elements, amateur design, cartoonish appearance, "
        "watermarks, irrelevant decorative elements, cluttered layout, poor spacing, "
        "missing essential event information, unprofessional typography, emojis, decorative symbols."
    )
    
    style = get_dynamic_style(category, event_type, tone)
    style_map = {
        "economy": f"{style}, clean readable text hierarchy, high contrast, essential information clearly displayed, professional but cost-effective design.",
        "balanced": f"{style}, professional typography hierarchy, high contrast text, photorealistic design, well-organized information layout, premium feel.",
        "premium": f"{style}, LUXURY typography with perfect information hierarchy, ultra-realistic design, professional photography quality, perfect lighting, high-end marketing materials, crystal clear text at all levels, sophisticated premium layout."
    }
    
    base_prompt = (
        f"Create a professional FLYER (portrait layout) for: '{title}' - {description}\n"
        f"Category: {category} | Type: {event_type} | Tone: {tone}\n"
        f"Requirements: {style_map[cost_mode]}\n"
        f"Context: {context if context else 'Standard professional event'}\n"
        f"CRITICAL: Include ALL event details prominently with large, readable fonts.\n"
        f"Use high contrast colors and professional design.\n"
        f"Focus on {category.lower()} themes and {tone.lower()} aesthetic.\n"
        f"Ensure all text is perfectly readable and well-organized."
    )
    
    if len(base_prompt) > 3500:
        base_prompt = PromptOptimizer.compress_prompt(base_prompt, 0.4)
    
    prompt = base_prompt
    start = time.time()
    
    cache_key = cache._get_cache_key(prompt, image_size, cost_mode, "flyer")
    cached_result = cache.get(cache_key)
    
    if cached_result:
        analytics.record_request(0, 0, time.time() - start, from_cache=True)
        import base64
        try:
            image_url = base64.b64decode(cached_result)
            print(f"Cache hit - decoded {len(image_url)} bytes")
        except Exception as e:
            image_url = cached_result  # if already bytes
            print(f"Cache hit - using cached bytes: {len(image_url) if hasattr(image_url, '__len__') else 'N/A'}")
    else:
        print("No cache hit - making API call")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    n=1,
                    size=image_size,
                    quality="hd" if cost_mode=="premium" else "standard",
                    response_format="b64_json"
                )
                image_b64 = response.data[0].b64_json
                import base64, io
                image_bytes = base64.b64decode(image_b64)
                cache.set(cache_key, image_b64)  # cache b64 string
                image_url = image_bytes
                print(f"API call successful - generated {len(image_url)} bytes")
                
                cost = 0.04 if cost_mode=="premium" else 0.02
                analytics.record_request(cost, count_tokens(prompt), time.time() - start)
                break
            except Exception as e:
                print(f"DALL-E Flyer Error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    analytics.record_request(0, 0, time.time() - start, error=True)
                    print(f"All retries failed - returning empty bytes")
                    return b"", {"error": str(e), "Time taken (s)": round(time.time() - start, 2)}
                time.sleep(2 ** attempt)
    end = time.time()
    prompt_tokens = count_tokens(prompt)
    completion_tokens = 0
    cost_map = {"1024x1024": 0.02, "1792x1024": 0.04, "1024x1792": 0.04}
    cost = 0.04 if cost_mode=="premium" else cost_map.get(image_size, 0.02)
    logs = {
        "Prompt tokens": prompt_tokens,
        "Completion tokens": completion_tokens,
        "Total tokens": prompt_tokens,
        "Time taken (s)": round(end - start, 2),
        "Estimated cost ($)": f"${cost:.5f}",
        "Model": "dall-e-3",
        "Prompt": prompt,
        "Cost mode": cost_mode,
        "Image size": image_size
    }
    print(f"Returning image_url: type={type(image_url)}, length={len(image_url) if hasattr(image_url, '__len__') else 'N/A'}")
    return image_url, logs

def generate_banner_image(title, description, category, event_type, tone, context=None, cost_mode="balanced", image_size="1792x1024"):
    example = get_flyer_examples(category, event_type, tone)
    event_details = extract_event_details(context)
    
    banner_specific_requirements = (
        "BANNER DESIGN SPECIFICATIONS:\n"
        "- BANNERS are LANDSCAPE orientation (horizontal) for digital displays and web use\n"
        "- Focus on VISUAL IMPACT with minimal but essential text\n"
        "- Optimized for: websites, social media headers, digital displays, presentations\n"
        "- Use WIDE layout design principles with horizontal text flow\n"
        "- Emphasize BRAND IDENTITY and visual appeal over detailed information\n"
        "- Perfect for: event announcements, social media promotion, website headers\n"
        "- Keep text CONCISE but IMPACTFUL - title and key details only\n"
    )
    
    text_optimization = (
        "BANNER TEXT REQUIREMENTS:\n"
        "- TITLE: Use HUGE, BOLD fonts optimized for horizontal layout\n"
        "- KEY INFO: Only essential details (date, time) in medium fonts\n"
        "- MINIMAL TEXT: Focus on visual impact rather than detailed information\n"
        "- HORIZONTAL TEXT FLOW: Arrange text to work with wide format\n"
        "- MAXIMUM CONTRAST: Ensure text stands out against background\n"
        "- STRATEGIC PLACEMENT: Position text for maximum visual impact\n"
        "- READABLE FROM DISTANCE: Text must be visible in small thumbnail sizes\n"
    )
    
    event_info_integration = ""
    if event_details['time'] or event_details['date'] or event_details['speakers'] or event_details['location'] or event_details['online_offline']:
        event_info_integration += f"KEY EVENT INFORMATION FOR BANNER (concise but impactful):\n"
        if event_details['date']:
            event_info_integration += f"- DATE: {event_details['date']} (Display clearly)\n"
        if event_details['time']:
            event_info_integration += f"- TIME: {event_details['time']}\n"
        if event_details['speakers']:
            event_info_integration += f"- FEATURING: {event_details['speakers']} (Prominent speaker names)\n"
        if event_details['location']:
            event_info_integration += f"- LOCATION: {event_details['location']}\n"
        if event_details['online_offline']:
            event_info_integration += f"- FORMAT: {event_details['online_offline'].upper()}\n"
        event_info_integration += "Present this information with IMPACT and CLARITY in the banner layout. Use strategic text placement.\n"
    elif context:
        event_info_integration += f"CONTEXT FOR BANNER:\n- {context}\nIntegrate key details from this context into the banner design.\n"
    
    realism_enhancement = (
        "BANNER VISUAL REQUIREMENTS:\n"
        "- Use STUNNING photorealistic backgrounds and elements\n"
        "- Apply CINEMATIC lighting and professional photography quality\n"
        "- Create WIDE-FORMAT composition with horizontal flow\n"
        "- Use HIGH-IMPACT visual elements suitable for digital display\n"
        "- Apply PROFESSIONAL color grading and visual effects\n"
        "- Ensure SCALABILITY for various digital platform sizes\n"
        "- Focus on VISUAL STORYTELLING through imagery\n"
        "- Use PREMIUM design aesthetics for digital marketing\n"
    )
    
    negative_prompt = (
        "STRICTLY AVOID: Cluttered text, vertical layout elements, too much text, "
        "poor horizontal composition, low contrast, pixelated elements, amateur design, "
        "inappropriate aspect ratio usage, text that's too small for banner format, "
        "busy backgrounds that interfere with text readability, emojis, decorative symbols."
    )
    
    style = get_dynamic_style(category, event_type, tone)
    style_map = {
        "economy": f"{style}, clean horizontal layout, high contrast minimal text, professional digital banner design, cost-effective but impactful.",
        "balanced": f"{style}, professional banner typography, cinematic horizontal composition, photorealistic design, optimized for digital platforms.",
        "premium": f"{style}, LUXURY banner design with cinematic quality, ultra-realistic horizontal composition, professional photography quality, perfect for high-end digital marketing, stunning visual impact."
    }
    
    base_prompt = (
        f"Create a professional BANNER (landscape layout) for: '{title}' - {description}\n"
        f"Category: {category} | Type: {event_type} | Tone: {tone}\n"
        f"Requirements: {style_map[cost_mode]}\n"
        f"Context: {context if context else 'Standard professional event'}\n"
        f"CRITICAL: Include key event details with large, readable fonts.\n"
        f"Use high contrast colors and professional design for digital display.\n"
        f"Focus on {category.lower()} themes and {tone.lower()} aesthetic.\n"
        f"Optimize for horizontal layout with impactful visual design."
    )
    
    if len(base_prompt) > 3500:
        base_prompt = PromptOptimizer.compress_prompt(base_prompt, 0.4)
    
    prompt = base_prompt
    
    start = time.time()
    
    cache_key = cache._get_cache_key(prompt, image_size, cost_mode, "banner")
    cached_result = cache.get(cache_key)
    
    if cached_result:
        analytics.record_request(0, 0, time.time() - start, from_cache=True)
        import base64
        try:
            image_url = base64.b64decode(cached_result)
            print(f"Banner cache hit - decoded {len(image_url)} bytes")
        except Exception as e:
            image_url = cached_result  # if already bytes
            print(f"Banner cache hit - using cached bytes: {len(image_url) if hasattr(image_url, '__len__') else 'N/A'}")
    else:
        print("No banner cache hit - making API call")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    n=1,
                    size=image_size,
                    quality="hd" if cost_mode=="premium" else "standard",
                    response_format="b64_json"
                )
                image_b64 = response.data[0].b64_json
                import base64
                image_bytes = base64.b64decode(image_b64)
                cache.set(cache_key, image_b64)
                image_url = image_bytes
                print(f"Banner API call successful - generated {len(image_url)} bytes")
                
                cost = 0.04 if cost_mode=="premium" else 0.02
                analytics.record_request(cost, count_tokens(prompt), time.time() - start)
                break
            except Exception as e:
                print(f"DALL-E Banner Error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    analytics.record_request(0, 0, time.time() - start, error=True)
                    return b"", {"error": str(e), "Time taken (s)": round(time.time() - start, 2)}
                time.sleep(2 ** attempt)
    
    end = time.time()
    
    prompt_tokens = count_tokens(prompt)
    completion_tokens = 0
    cost_map = {"1024x1024": 0.02, "1792x1024": 0.04, "1024x1792": 0.04}
    cost = 0.04 if cost_mode=="premium" else cost_map.get(image_size, 0.04)
    
    logs = {
        "Prompt tokens": prompt_tokens,
        "Completion tokens": completion_tokens,
        "Total tokens": prompt_tokens,
        "Time taken (s)": round(end - start, 2),
        "Estimated cost ($)": f"${cost:.5f}",
        "Model": "dall-e-3",
        "Prompt": prompt,
        "Cost mode": cost_mode,
        "Image size": image_size,
        "Design type": "Banner"
    }
    
    print(f"Returning banner image_url: type={type(image_url)}, length={len(image_url) if hasattr(image_url, '__len__') else 'N/A'}")
    return image_url, logs

def get_global_analytics():
    return {
        "total_requests": analytics.metrics['total_requests'],
        "cache_hits": analytics.metrics['cache_hits'],
        "cache_hit_rate": f"{(analytics.metrics['cache_hits'] / max(analytics.metrics['total_requests'], 1)) * 100:.1f}%",
        "total_cost": f"${analytics.metrics['total_cost']:.4f}",
        "total_tokens": analytics.metrics['total_tokens'],
        "avg_response_time": f"{analytics.metrics['avg_response_time']:.2f}s",
        "error_rate": f"{analytics.metrics['error_rate'] * 100:.1f}%",
        "efficiency_score": f"{analytics.get_efficiency_score():.1f}%",
        "cost_savings": f"${(analytics.metrics['cache_hits'] * 0.002):.4f}",
        "recommendations": get_optimization_recommendations()
    }

def get_optimization_recommendations():
    recommendations = []
    cache_rate = analytics.metrics['cache_hits'] / max(analytics.metrics['total_requests'], 1)
    avg_cost = analytics.metrics['total_cost'] / max(analytics.metrics['total_requests'], 1)
    
    if cache_rate < 0.2:
        recommendations.append("Use similar content parameters to boost cache efficiency (target: 60%+)")
    elif cache_rate < 0.5:
        recommendations.append("Good cache performance - try reusing successful prompts")
    
    if avg_cost > 0.008:
        recommendations.append("High cost per request - switch to economy mode to reduce by 40%")
    elif avg_cost > 0.005:
        recommendations.append("Moderate costs - consider economy mode for non-critical requests")
    
    if analytics.metrics['avg_response_time'] > 8:
        recommendations.append("Slow responses detected - cache will improve this significantly")
    elif analytics.metrics['avg_response_time'] > 5:
        recommendations.append("Response time acceptable - will improve with cache hits")
    
    if analytics.metrics['total_tokens'] / max(analytics.metrics['total_requests'], 1) > 1500:
        recommendations.append("High token usage - use economy mode for 25% token reduction")
    
    if analytics.metrics['error_rate'] > 0.05:
        recommendations.append("Error rate detected - verify API key and network stability")
    
    efficiency_score = analytics.get_efficiency_score()
    if efficiency_score > 80:
        recommendations.append("Excellent performance - system optimized")
    elif efficiency_score > 60:
        recommendations.append("Good performance - minor optimizations available")
    elif efficiency_score > 40:
        recommendations.append("Moderate efficiency - implement caching strategies")
    else:
        recommendations.append("Low efficiency - review cost mode and enable caching")
    
    return recommendations

def reset_analytics():
    global analytics
    analytics = PerformanceAnalytics()
    return "Analytics reset successfully" 