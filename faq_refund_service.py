from event_llm_core import generate_faqs_and_refund_policy
import argparse

def main():
    parser = argparse.ArgumentParser(description="Event FAQ & Refund Policy Generation Service")
    parser.add_argument('--title', required=True, help='Event title')
    parser.add_argument('--description', required=True, help='Event description')
    parser.add_argument('--category', required=True, help='Event category')
    parser.add_argument('--event_type', required=True, help='Event type')
    parser.add_argument('--tone', required=True, help='Tone of the event')
    parser.add_argument('--context', required=False, default=None, help='Optional context')
    parser.add_argument('--cost_mode', choices=['economy', 'balanced', 'premium'], default='balanced', help='Cost/quality mode')
    args = parser.parse_args()
    print(f"[FAQ/Refund Service] Generating FAQs and refund policy")
    print(f"[FAQ/Refund Service] Title: {args.title}")
    print(f"[FAQ/Refund Service] Description: {args.description}")
    print(f"[FAQ/Refund Service] Category: {args.category}")
    print(f"[FAQ/Refund Service] Event Type: {args.event_type}")
    print(f"[FAQ/Refund Service] Tone: {args.tone}")
    print(f"[FAQ/Refund Service] Context: {args.context}")
    print(f"[FAQ/Refund Service] Cost Mode: {args.cost_mode}")
    print("-" * 50)
    faqs, refund_policy, logs = generate_faqs_and_refund_policy(
        args.title,
        args.description,
        args.category,
        args.event_type,
        args.tone,
        args.context,
        args.cost_mode
    )
    print("[FAQ/Refund Service] Generation Logs:")
    for k, v in logs.items():
        print(f"  {k}: {v}")
    print(f"[FAQ/Refund Service] Generated FAQs:")
    for i, faq in enumerate(faqs, 1):
        print(f"  Q{i}: {faq['question']}")
        print(f"  A{i}: {faq['answer']}")
    print(f"[FAQ/Refund Service] Generated Refund Policy:")
    print(f"  {refund_policy}")

if __name__ == "__main__":
    main() 