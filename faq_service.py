from event_llm_core import generate_faqs
import argparse

def main():
    parser = argparse.ArgumentParser(description="Event FAQ Generation Service")
    parser.add_argument('--title', required=True, help='Event title')
    parser.add_argument('--description', required=True, help='Event description')
    parser.add_argument('--category', required=True, help='Event category')
    parser.add_argument('--event_type', required=True, help='Event type')
    parser.add_argument('--tone', required=True, help='Tone of the event')
    parser.add_argument('--context', required=False, default=None, help='Optional context')
    parser.add_argument('--cost_mode', choices=['economy', 'balanced', 'premium'], default='balanced', help='Cost/quality mode')
    
    args = parser.parse_args()
    
    print(f"[FAQ Service] Generating FAQs")
    print(f"[FAQ Service] Title: {args.title}")
    print(f"[FAQ Service] Description: {args.description}")
    print(f"[FAQ Service] Category: {args.category}")
    print(f"[FAQ Service] Event Type: {args.event_type}")
    print(f"[FAQ Service] Tone: {args.tone}")
    print(f"[FAQ Service] Context: {args.context}")
    print(f"[FAQ Service] Cost Mode: {args.cost_mode}")
    print("-" * 50)
    
    faqs, logs = generate_faqs(
        args.title,
        args.description,
        args.category,
        args.event_type,
        args.tone,
        args.context,
        args.cost_mode
    )
    
    print("[FAQ Service] Generation Logs:")
    for k, v in logs.items():
        print(f"  {k}: {v}")
    
    print(f"[FAQ Service] Generated {len(faqs)} FAQs:")
    for i, faq in enumerate(faqs, 1):
        print(f"  Q{i}: {faq['question']}")
        print(f"  A{i}: {faq['answer']}")
        print()

if __name__ == "__main__":
    main() 