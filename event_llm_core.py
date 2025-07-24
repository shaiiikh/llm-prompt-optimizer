import json
import os
import time
from dotenv import load_dotenv
from difflib import get_close_matches
import streamlit as st
from openai import OpenAI
import random

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
            frequency_penalty=0.6,
            presence_penalty=0.4
        )
        return response.choices[0].message.content.strip()
    
    result = call_llm(system_msg, user_msg, max_tokens, temperature)
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
        
        result2 = call_llm(retry_system, retry_user, max_tokens + 20, temperature + 0.1)
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
        "Titles generated": len(titles)
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

def generate_faqs_and_refund_policy(title, description, category, event_type, tone, context=None, cost_mode="balanced"):
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
        f"Based on the following event details, generate at least 5 relevant, clear, and professional FAQs (with answers) and a concise, fair refund policy.\n"
        f"Event Title: {title}\n"
        f"Description: {description}\n"
        f"Category: {category}\n"
        f"Event Type: {event_type}\n"
        f"Tone: {tone}\n"
        f"{f'Context: {context}' if context else ''}\n\n"
        f"Requirements:\n"
        f"1. Create at least 5 FAQs that directly address likely questions about this specific event\n"
        f"2. Make answers informative, helpful, and in a {tone.lower()} tone\n"
        f"3. Create a fair, clear refund policy appropriate for a {category} {event_type}\n"
        f"4. Format as shown in the examples below\n\n"
        f"{few_shot}\n"
        f"Now generate FAQs and a refund policy for this event. Format:\nFAQs:\nQ: ...\nA: ...\n...\nRefund Policy:\n..."
    )
    
    start = time.time()
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1200,
            temperature=0.7,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.3
        )
        output = response.choices[0].message.content.strip()
    except Exception as e:
        return [], "", {"error": str(e)}
    end = time.time()
    
    faqs = []
    refund_policy = ""
    
    if "Refund Policy:" in output:
        parts = output.split("Refund Policy:", 1)
        faqs_part = parts[0]
        refund_policy = parts[1].strip()
    else:
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
    
    if not refund_policy and event_type in refund_policies:
        refund_policy = refund_policies[event_type]
    elif not refund_policy:
        refund_policy = default_policy
    
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
    return faqs, refund_policy, logs

def get_flyer_examples(category, event_type, tone):
    examples = [
        {"title": "Tech Leadership Summit", "description": "A premier gathering for technology leaders to explore innovation and future trends.", "category": "Technology", "event_type": "Conference", "tone": "Professional", "style": "Modern, blue and white, digital motifs, clean layout, bold headline, subtle tech icons, no text overlays"},
        {"title": "Art & Culture Fest", "description": "A vibrant celebration of art, music, and culture for all ages.", "category": "Arts & Culture", "event_type": "Festival", "tone": "Creative", "style": "Colorful, artistic brush strokes, lively, festive, creative composition, minimal text"},
        {"title": "Business Growth Workshop", "description": "Unlock new strategies for business expansion and leadership.", "category": "Business", "event_type": "Workshop", "tone": "Professional", "style": "Corporate, clean, blue and gray, upward arrows, professional, minimal text"},
        {"title": "Health & Wellness Expo", "description": "Discover the latest in health, fitness, and wellness trends.", "category": "Health", "event_type": "Exhibition", "tone": "Friendly", "style": "Fresh, green and white, wellness icons, approachable, clean, minimal text"},
        {"title": "Kids Science Fair", "description": "A fun, interactive science fair for children and families.", "category": "Education", "event_type": "Exhibition", "tone": "Playful", "style": "Bright, playful, cartoon icons, fun layout, bold colors, minimal text"},
        {"title": "Luxury Gala Night", "description": "An exclusive evening gala for charity and networking.", "category": "Business", "event_type": "Gala", "tone": "Premium", "style": "Elegant, gold and black, luxury, minimal text, sophisticated layout"},
        {"title": "Startup Pitch Meetup", "description": "Pitch your startup to investors and network with founders.", "category": "Business", "event_type": "Meetup", "tone": "Innovative", "style": "Modern, energetic, startup icons, blue and orange, clean, minimal text"},
        {"title": "Sports Fan Fest", "description": "A festival for sports fans with games, food, and fun.", "category": "Sports", "event_type": "Festival", "tone": "Casual", "style": "Bold, energetic, sports icons, team colors, festive, minimal text"},
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
        return "Elegant, gold and black, luxury, minimal text, sophisticated layout"
    if category == "Education" and tone == "Playful":
        return "Bright, playful, cartoon icons, fun layout, bold colors, minimal text"
    if category == "Technology":
        return "Futuristic, blue tones, digital motifs, modern, clean, minimal text"
    if category == "Sports":
        return "Bold, energetic, sports icons, team colors, festive, minimal text"
    if category == "Arts & Culture":
        return "Colorful, artistic, creative, brush strokes, lively, minimal text"
    if tone == "Premium":
        return "Elegant, luxury, gold accents, high-end, minimal text"
    if tone == "Friendly":
        return "Fresh, green and white, approachable, clean, minimal text"
    return "Modern, creative, professional, vibrant, high quality, visually engaging, minimal text"

def generate_flyer_image(title, description, category, event_type, tone, context=None, cost_mode="balanced", image_size="1024x1024"):
    example = get_flyer_examples(category, event_type, tone)
    few_shot = f"Example Flyer:\nTitle: {example['title']}\nDescription: {example['description']}\nCategory: {example['category']}\nEvent Type: {example['event_type']}\nTone: {example['tone']}\nStyle: {example['style']}\n---\n"
    negative_prompt = "No watermarks, no irrelevant icons, no excessive text, no blurry backgrounds, no borders, no QR codes, no logos, no faces, no hands."
    randomization = random.choice([
        "Try a modern or abstract background.",
        "Use a dynamic composition.",
        "Incorporate subtle gradients.",
        "Add a creative border effect.",
        "Use a unique color palette.",
        "Try a minimalist icon set."
    ])
    extra_context = ""
    if context:
        extra_context += f"\nAdditional context: {context}"
        if any(x in context.lower() for x in ["audience", "for kids", "adults", "professionals", "students"]):
            extra_context += "\nAudience details included."
        if any(x in context.lower() for x in ["summer", "winter", "spring", "fall", "autumn", "holiday", "season"]):
            extra_context += "\nSeasonal theme included."
        if any(x in context.lower() for x in ["theme", "layout", "color", "font", "palette"]):
            extra_context += "\nExplicit layout, color, or font guidance included."
    style = get_dynamic_style(category, event_type, tone)
    style_map = {
        "economy": "Minimalist, simple, flat colors, low detail, no text overlays, efficient for digital use.",
        "balanced": style,
        "premium": f"{style}, ultra-creative, highly detailed, premium, eye-catching, suitable for print and digital, artistic, best for marketing, dynamic composition, rich color, subtle branding, no watermarks."
    }
    prompt = (
        f"You are a professional event flyer/banner designer.\n"
        f"Always generate visually compelling, professional, and creative flyers.\n"
        f"Use modern design, clear event theme, and vibrant but clean composition.\n"
        f"Avoid text overlays except for the main title.\n"
        f"Incorporate subtle icons or motifs relevant to the event type and category.\n"
        f"Use color schemes and style that match the tone.\n"
        f"{few_shot}"
        f"Now generate a flyer/banner for:\n"
        f"Title: {title}\nDescription: {description}\nCategory: {category}\nEvent Type: {event_type}\nTone: {tone}."
        f"\nStyle: {style_map[cost_mode]}"
        f"\n{negative_prompt}"
        f"\n{randomization}"
        f"{extra_context}"
    )
    start = time.time()
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size=image_size,
            quality="hd" if cost_mode=="premium" else "standard",
            response_format="url"
        )
        image_url = response.data[0].url
    except Exception as e:
        return "", {"error": str(e)}
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
    return image_url, logs 