import streamlit as st
import os

try:
    from event_llm_core import generate_titles, generate_description, generate_flyer_image, generate_faqs_and_refund_policy, fuzzy_correct
except Exception as e:
    st.error("**Configuration Error**")
    st.error("OpenAI API key is missing or invalid.")
    st.markdown("""
    ### How to fix this:
    
    **For Streamlit Cloud:**
    1. Go to your app settings
    2. Click on "Secrets" 
    3. Add: `OPENAI_API_KEY = "your_api_key_here"`
    
    **For local development:**
    1. Create a `.env` file
    2. Add: `OPENAI_API_KEY=your_api_key_here`
    
    **Get your API key:**
    - Visit: https://platform.openai.com/api-keys
    - Create a new secret key
    - Copy and paste it in the configuration above
    """)
    st.stop()

st.set_page_config(page_title="EC - 172", layout="wide")

st.markdown("""
<style>
section.main > div:first-child {background: #f8fafc; border-radius: 12px; padding: 2rem 2rem 1rem 2rem; box-shadow: 0 2px 8px #0001;}
.stSelectbox [data-baseweb="select"] > div {border-radius: 8px;}
.stButton > button {border-radius: 8px; background: #2563eb; color: #fff; font-weight: 600;}
.stSlider > div {color: #2563eb;}
.stTextInput > div > input {border-radius: 8px;}
.stTextArea > div > textarea {border-radius: 8px;}
.optimization-tip {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
    border-left: 4px solid #4299e1;
}
</style>
""", unsafe_allow_html=True)

st.title("EC-172")
st.write("Generate event titles, descriptions, flyers/banners, FAQs, and refund policies with advanced prompt engineering.")

def get_optimization_tip(category, event_type, tone):
    tips = {
        ("Technology", "Conference", "Professional"): "Pro tip: Technology conferences perform best with titles that emphasize innovation, future trends, and networking opportunities.",
        ("Technology", "Workshop", "Creative"): "Pro tip: Creative technology workshops work best when titles suggest hands-on learning and innovation.",
        ("Business", "Workshop", "Formal"): "Pro tip: Formal business workshops should highlight specific skills, ROI, and executive-level insights.",
        ("Business", "Conference", "Professional"): "Pro tip: Professional business conferences perform best with titles emphasizing leadership and strategic outcomes.",
        ("Education", "Seminar", "Creative"): "Pro tip: Creative education seminars work best when titles suggest transformation and hands-on learning.",
        ("Education", "Conference", "Innovative"): "Pro tip: Innovative education conferences should emphasize future learning methods and technology integration.",
        ("Health", "Workshop", "Friendly"): "Pro tip: Friendly health workshops perform best with approachable titles that emphasize wellness and community.",
        ("Entertainment", "Festival", "Casual"): "Pro tip: Casual entertainment festivals work best with fun, energetic titles that create excitement.",
        ("Sports", "Conference", "Professional"): "Pro tip: Professional sports conferences should emphasize performance, strategy, and industry insights.",
        ("Arts & Culture", "Exhibition", "Creative"): "Pro tip: Creative arts exhibitions work best with inspiring titles that evoke curiosity and artistic expression."
    }
    
    key = (category, event_type, tone)
    if key in tips:
        return tips[key]
    
    return f"Pro tip: {tone} {event_type}s in {category} perform best when titles clearly communicate the unique value and target outcome."

def suggest_optimal_settings(category, event_type):
    suggestions = {
        ("Technology", "Conference"): {"tone": "Professional", "titles": 5, "desc_length": 1200},
        ("Technology", "Workshop"): {"tone": "Creative", "titles": 4, "desc_length": 800},
        ("Business", "Seminar"): {"tone": "Formal", "titles": 3, "desc_length": 1000},
        ("Business", "Conference"): {"tone": "Professional", "titles": 5, "desc_length": 1400},
        ("Education", "Conference"): {"tone": "Innovative", "titles": 5, "desc_length": 1400},
        ("Education", "Workshop"): {"tone": "Creative", "titles": 4, "desc_length": 900},
        ("Health", "Workshop"): {"tone": "Friendly", "titles": 4, "desc_length": 900},
        ("Health", "Seminar"): {"tone": "Professional", "titles": 3, "desc_length": 800},
        ("Entertainment", "Festival"): {"tone": "Casual", "titles": 5, "desc_length": 1000},
        ("Sports", "Conference"): {"tone": "Professional", "titles": 4, "desc_length": 1200},
        ("Arts & Culture", "Exhibition"): {"tone": "Creative", "titles": 5, "desc_length": 1100}
    }
    
    key = (category, event_type)
    return suggestions.get(key, {"tone": "Professional", "titles": 3, "desc_length": 800})

if 'generated_titles' not in st.session_state:
    st.session_state.generated_titles = []
if 'final_title' not in st.session_state:
    st.session_state.final_title = ""
if 'description' not in st.session_state:
    st.session_state.description = ""
if 'final_description' not in st.session_state:
    st.session_state.final_description = ""
if 'flyer_image_url' not in st.session_state:
    st.session_state.flyer_image_url = ""
if 'final_flyer' not in st.session_state:
    st.session_state.final_flyer = ""
if 'faqs' not in st.session_state:
    st.session_state.faqs = []
if 'final_faqs' not in st.session_state:
    st.session_state.final_faqs = []
if 'refund_policy' not in st.session_state:
    st.session_state.refund_policy = ""
if 'final_refund_policy' not in st.session_state:
    st.session_state.final_refund_policy = ""
if 'title_logs' not in st.session_state:
    st.session_state.title_logs = None
if 'desc_logs' not in st.session_state:
    st.session_state.desc_logs = None
if 'flyer_logs' not in st.session_state:
    st.session_state.flyer_logs = None
if 'faq_logs' not in st.session_state:
    st.session_state.faq_logs = None

category_options = ["Select event category", "Technology", "Business", "Education", "Health", "Entertainment", "Sports", "Arts & Culture", "Other"]
event_type_options = ["Select event type", "Conference", "Workshop", "Seminar", "Webinar", "Festival", "Exhibition", "Meetup", "Other"]
tone_options = ["Select tone of event", "Professional", "Casual", "Formal", "Creative", "Premium", "Innovative", "Friendly", "Corporate", "Other"]

st.markdown("## Title Generation")

col1, col2, col3 = st.columns(3)

with col1:
    title_category = st.selectbox("Category for Titles", category_options, index=0, key="title_category")
    if title_category == "Other":
        custom_title_category = st.text_input("Custom category", key="custom_title_category")
        if custom_title_category:
            suggestion = fuzzy_correct(custom_title_category, category_options[1:-1])
            if suggestion != custom_title_category:
                st.info(f"Did you mean: {suggestion}?")

with col2:
    title_event_type = st.selectbox("Event Type for Titles", event_type_options, index=0, key="title_event_type")
    if title_event_type == "Other":
        custom_title_event_type = st.text_input("Custom event type", key="custom_title_event_type")
        if custom_title_event_type:
            suggestion = fuzzy_correct(custom_title_event_type, event_type_options[1:-1])
            if suggestion != custom_title_event_type:
                st.info(f"Did you mean: {suggestion}?")

with col3:
    title_tone = st.selectbox("Tone for Titles", tone_options, index=0, key="title_tone")
    if title_tone == "Other":
        custom_title_tone = st.text_input("Custom tone", key="custom_title_tone")
        if custom_title_tone:
            suggestion = fuzzy_correct(custom_title_tone, tone_options[1:-1])
            if suggestion != custom_title_tone:
                st.info(f"Did you mean: {suggestion}?")

if title_category != "Select event category" and title_event_type != "Select event type":
    optimal = suggest_optimal_settings(title_category, title_event_type)
    st.markdown(f'<div class="optimization-tip">Optimization Suggestion: For {title_category} {title_event_type}s, consider using {optimal["tone"]} tone with {optimal["titles"]} titles for best results.</div>', unsafe_allow_html=True)

if title_category != "Select event category" and title_event_type != "Select event type" and title_tone != "Select tone of event":
    tip = get_optimization_tip(title_category, title_event_type, title_tone)
    st.info(tip)

with st.form("title_form", clear_on_submit=False):
    cost_mode = st.selectbox("Cost Optimization", ["balanced", "economy", "premium"], key="cost_mode")
    num_titles = st.slider("Number of Titles (max 5)", min_value=1, max_value=5, value=3)
    title_context = st.text_input("Context for Titles (optional)", placeholder="e.g., Focus on AI and machine learning trends")
    generate_titles_btn = st.form_submit_button("Generate Titles")

if generate_titles_btn:
    with st.spinner("Generating titles with advanced prompt engineering..."):
        try:
            final_category = custom_title_category if title_category == "Other" and 'custom_title_category' in locals() and custom_title_category else title_category
            final_event_type = custom_title_event_type if title_event_type == "Other" and 'custom_title_event_type' in locals() and custom_title_event_type else title_event_type
            final_tone = custom_title_tone if title_tone == "Other" and 'custom_title_tone' in locals() and custom_title_tone else title_tone
            
            titles, logs = generate_titles(
                final_category if final_category != "Select event category" else "Business",
                final_event_type if final_event_type != "Select event type" else "Conference",
                final_tone if final_tone != "Select tone of event" else "Professional",
                num_titles,
                title_context if title_context else None,
                cost_mode
            )
            st.session_state.generated_titles = titles
            st.session_state.title_logs = logs
        except Exception as e:
            st.error(f"Error generating titles: {str(e)}")
            st.error("Please try again or check your API key.")

if st.session_state.get("generated_titles"):
    st.markdown("### Generated Titles:")
    for i, title in enumerate(st.session_state.generated_titles, 1):
        st.markdown(f'<div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #2563eb; color: #333; margin-bottom: 0.5rem;">{i}. {title}</div>', unsafe_allow_html=True)
    st.download_button("Download Titles", "\n".join(st.session_state.generated_titles), file_name="event_titles.txt", mime="text/plain", key="download_titles_btn")
    
    if st.session_state.title_logs:
        show_title_analytics = st.button("View Title Generation Analytics", key="title_analytics_btn")
        if show_title_analytics:
            st.markdown("### Title Generation Analytics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Prompt Tokens", st.session_state.title_logs.get('Prompt tokens', 'N/A'))
                st.metric("Total Tokens", st.session_state.title_logs.get('Total tokens', 'N/A'))
            with col2:
                st.metric("Completion Tokens", st.session_state.title_logs.get('Completion tokens', 'N/A'))
                st.metric("Generation Time", f"{st.session_state.title_logs.get('Time taken (s)', 'N/A')}s")
            st.metric("Cost", st.session_state.title_logs.get('Estimated cost ($)', 'N/A'))
            st.markdown(f"**Model Used:** {st.session_state.title_logs.get('Model', 'gpt-3.5-turbo')}")
            with st.expander("Show Prompt Preview"):
                st.markdown(f"""
**System Prompt:**
```
{st.session_state.title_logs.get('System prompt', '')}
```
**User Prompt:**
```
{st.session_state.title_logs.get('User prompt', '')}
```
""", unsafe_allow_html=True)
    
    st.markdown("### Select or Create Your Title:")
    title_options = ["Select a title option..."] + [f"Use: {title}" for title in st.session_state.generated_titles] + ["Write my own custom title"]
    
    title_choice = st.selectbox("Choose how you want to proceed:", title_options, key="title_choice")
    
    if title_choice.startswith("Use: "):
        selected_generated_title = title_choice[5:]
        st.info(f"Selected title: **{selected_generated_title}**")
        
        edit_option = st.radio("What would you like to do?", 
                              ["Use this title as-is", "Edit this title"], 
                              key="edit_option")
        
        if edit_option == "Use this title as-is":
            st.session_state.final_title = selected_generated_title
            st.success(f"Final title: **{selected_generated_title}**")
        else:
            edited_title = st.text_input("Edit the title:", 
                                       value=selected_generated_title, 
                                       key="edit_selected_title")
            if edited_title:
                st.session_state.final_title = edited_title
                st.success(f"Final edited title: **{edited_title}**")
    
    elif title_choice == "Write my own custom title":
        custom_title = st.text_input("Write your own title:", 
                                   placeholder="Enter your custom event title...", 
                                   key="custom_title_input")
        if custom_title:
            suggestion = fuzzy_correct(custom_title, st.session_state.generated_titles)
            if suggestion != custom_title and suggestion in st.session_state.generated_titles:
                st.info(f"Did you mean one of our generated titles: **{suggestion}**?")
                use_suggestion = st.checkbox(f"Use '{suggestion}' instead?", key="use_fuzzy_suggestion")
                if use_suggestion:
                    st.session_state.final_title = suggestion
                    st.success(f"Final title (suggested): **{suggestion}**")
                else:
                    st.session_state.final_title = custom_title
                    st.success(f"Final custom title: **{custom_title}**")
            else:
                st.session_state.final_title = custom_title
                st.success(f"Final custom title: **{custom_title}**")

if st.session_state.get("final_title"):
    st.markdown("## Description Generation")
    
    desc_use_same = st.radio(
        "Description Content:",
        ["Use same title and settings as above", "Enter custom description parameters"],
        key="desc_use_same",
        help="Choose whether to use the selected title and previous settings or enter custom parameters."
    )
    
    with st.form("description_form", clear_on_submit=False):
        if desc_use_same == "Use same title and settings as above":
            desc_title = st.text_input("Title for Description", value=st.session_state.final_title, key="desc_title_input", disabled=True)
            desc_category = st.selectbox("Category for Description", ["Technology", "Business", "Education", "Health", "Entertainment", "Sports", "Arts & Culture", "Other"], 
                                       index=max(0, ["Technology", "Business", "Education", "Health", "Entertainment", "Sports", "Arts & Culture", "Other"].index(title_category) if title_category != "Select event category" else 0), 
                                       key="desc_category", disabled=True)
            desc_event_type = st.selectbox("Event Type for Description", ["Conference", "Workshop", "Seminar", "Webinar", "Festival", "Exhibition", "Meetup", "Other"],
                                         index=max(0, ["Conference", "Workshop", "Seminar", "Webinar", "Festival", "Exhibition", "Meetup", "Other"].index(title_event_type) if title_event_type != "Select event type" else 0),
                                         key="desc_event_type", disabled=True)
            desc_tone = st.selectbox("Tone for Description", ["Professional", "Casual", "Formal", "Creative", "Premium", "Innovative", "Friendly", "Corporate", "Other"],
                                   index=max(0, ["Professional", "Casual", "Formal", "Creative", "Premium", "Innovative", "Friendly", "Corporate", "Other"].index(title_tone) if title_tone != "Select tone of event" else 0),
                                   key="desc_tone", disabled=True)
            desc_context = st.text_input("Context for Description (optional)", value=title_context or "", key="desc_context", disabled=True)
            desc_cost_mode = st.selectbox("Description Cost Mode", ["balanced", "economy", "premium"], index=["balanced", "economy", "premium"].index(cost_mode), key="desc_cost_mode", disabled=True)
        else:
            desc_title = st.text_input("Title for Description", value=st.session_state.final_title, key="desc_title_input_custom")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                desc_category = st.selectbox("Category for Description", category_options, index=0, key="desc_category_custom")
                if desc_category == "Other":
                    custom_desc_category = st.text_input("Custom category", key="custom_desc_category")
                    if custom_desc_category:
                        suggestion = fuzzy_correct(custom_desc_category, category_options[1:-1])
                        if suggestion != custom_desc_category:
                            st.info(f"Did you mean: {suggestion}?")
            
            with col2:
                desc_event_type = st.selectbox("Event Type for Description", event_type_options, index=0, key="desc_event_type_custom")
                if desc_event_type == "Other":
                    custom_desc_event_type = st.text_input("Custom event type", key="custom_desc_event_type")
                    if custom_desc_event_type:
                        suggestion = fuzzy_correct(custom_desc_event_type, event_type_options[1:-1])
                        if suggestion != custom_desc_event_type:
                            st.info(f"Did you mean: {suggestion}?")
            
            with col3:
                desc_tone = st.selectbox("Tone for Description", tone_options, index=0, key="desc_tone_custom")
                if desc_tone == "Other":
                    custom_desc_tone = st.text_input("Custom tone", key="custom_desc_tone")
                    if custom_desc_tone:
                        suggestion = fuzzy_correct(custom_desc_tone, tone_options[1:-1])
                        if suggestion != custom_desc_tone:
                            st.info(f"Did you mean: {suggestion}?")
            
            desc_context = st.text_input("Context for Description (optional)", value="", key="desc_context_custom")
            desc_cost_mode = st.selectbox("Description Cost Mode", ["balanced", "economy", "premium"], key="desc_cost_mode_custom")
        
        max_chars = st.slider("Description Length (characters)", min_value=100, max_value=2000, value=800)
        generate_desc_btn = st.form_submit_button("Generate Description")

    if generate_desc_btn:
        with st.spinner("Generating description with advanced prompt engineering..."):
            try:
                if desc_use_same != "Use same title and settings as above":
                    final_desc_category = custom_desc_category if desc_category == "Other" and 'custom_desc_category' in locals() and custom_desc_category else desc_category
                    final_desc_event_type = custom_desc_event_type if desc_event_type == "Other" and 'custom_desc_event_type' in locals() and custom_desc_event_type else desc_event_type
                    final_desc_tone = custom_desc_tone if desc_tone == "Other" and 'custom_desc_tone' in locals() and custom_desc_tone else desc_tone
                else:
                    final_desc_category = desc_category
                    final_desc_event_type = desc_event_type
                    final_desc_tone = desc_tone
                
                description, logs = generate_description(
                    desc_title if desc_title else "Event Title",
                    final_desc_category if final_desc_category != "Select event category" else "Business",
                    final_desc_event_type if final_desc_event_type != "Select event type" else "Conference",
                    final_desc_tone if final_desc_tone != "Select tone of event" else "Professional",
                    desc_context if desc_context else None,
                    max_chars,
                    desc_cost_mode
                )
                st.session_state.description = description
                st.session_state.desc_logs = logs
            except Exception as e:
                st.error(f"Error generating description: {str(e)}")
                st.error("Please try again or check your API key.")

    if st.session_state.get("description"):
        st.markdown("### Generated Description:")
        st.markdown(f'<div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #28a745; color: #333;">{st.session_state.description}</div>', unsafe_allow_html=True)
        st.info(f"Description length: {len(st.session_state.description)} characters")
        st.download_button("Download as .txt", st.session_state.description, file_name="event_description.txt", mime="text/plain", key="download_desc_btn")
        
        if st.session_state.desc_logs:
            show_desc_analytics = st.button("View Description Generation Analytics", key="desc_analytics_btn")
            if show_desc_analytics:
                st.markdown("### Description Generation Analytics")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Prompt Tokens", st.session_state.desc_logs.get('Prompt tokens', 'N/A'))
                    st.metric("Total Tokens", st.session_state.desc_logs.get('Total tokens', 'N/A'))
                with col2:
                    st.metric("Completion Tokens", st.session_state.desc_logs.get('Completion tokens', 'N/A'))
                    st.metric("Generation Time", f"{st.session_state.desc_logs.get('Time taken (s)', 'N/A')}s")
                st.metric("Cost", st.session_state.desc_logs.get('Estimated cost ($)', 'N/A'))
                st.markdown(f"**Model Used:** {st.session_state.desc_logs.get('model', 'gpt-3.5-turbo')}")
                with st.expander("Show Prompt Preview"):
                    st.markdown(f"""
**System Prompt:**
```
{st.session_state.desc_logs.get('system_prompt', '')}
```
**User Prompt:**
```
{st.session_state.desc_logs.get('user_prompt', '')}
```
""", unsafe_allow_html=True)
        
        st.markdown("### Use This Description:")
        desc_options = ["Use generated description", "Edit generated description", "Write my own description"]
        desc_choice = st.selectbox("Choose how you want to proceed:", desc_options, key="desc_choice")
        
        if desc_choice == "Use generated description":
            st.session_state.final_description = st.session_state.description
            st.success(f"Using generated description ({len(st.session_state.description)} characters)")
        elif desc_choice == "Edit generated description":
            edited_desc = st.text_area("Edit the description:", 
                                     value=st.session_state.description, 
                                     key="edit_desc", height=150)
            if edited_desc:
                st.session_state.final_description = edited_desc
                st.success(f"Using edited description ({len(edited_desc)} characters)")
        else:
            custom_desc = st.text_area("Write your own description:", 
                                     placeholder="Enter your custom event description...", 
                                     key="custom_desc", height=150)
            if custom_desc:
                st.session_state.final_description = custom_desc
                st.success(f"Using custom description ({len(custom_desc)} characters)")

if st.session_state.get("final_title"):
    st.markdown("## Flyer/Banner Generation")
    
    flyer_use_same = st.radio(
        "Flyer Content:",
        ["Use selected title/description from above", "Enter custom flyer content"],
        key="flyer_use_same",
        help="Choose whether to use the selected title and description or enter custom content for your flyer."
    )
    
    with st.form("flyer_form", clear_on_submit=False):
        if flyer_use_same == "Use selected title/description from above":
            flyer_title = st.text_input("Flyer Title", value=st.session_state.final_title, key="flyer_title_input", disabled=True)
            flyer_description = st.text_area("Flyer Description", value=st.session_state.get("final_description", st.session_state.get("description", "")), key="flyer_desc_input", disabled=True)
        else:
            flyer_title = st.text_input("Flyer Title", value=st.session_state.final_title, key="flyer_title_input_custom")
            flyer_description = st.text_area("Flyer Description", value=st.session_state.get("final_description", ""), key="flyer_desc_input_custom")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            flyer_category = st.selectbox("Flyer Category", category_options, index=0, key="flyer_category")
            if flyer_category == "Other":
                custom_flyer_category = st.text_input("Custom category", key="custom_flyer_category")
                if custom_flyer_category:
                    suggestion = fuzzy_correct(custom_flyer_category, category_options[1:-1])
                    if suggestion != custom_flyer_category:
                        st.info(f"Did you mean: {suggestion}?")
        
        with col2:
            flyer_event_type = st.selectbox("Flyer Event Type", event_type_options + ["Gala"], index=0, key="flyer_event_type")
            if flyer_event_type == "Other":
                custom_flyer_event_type = st.text_input("Custom event type", key="custom_flyer_event_type")
                if custom_flyer_event_type:
                    suggestion = fuzzy_correct(custom_flyer_event_type, event_type_options[1:-1])
                    if suggestion != custom_flyer_event_type:
                        st.info(f"Did you mean: {suggestion}?")
        
        with col3:
            flyer_tone = st.selectbox("Flyer Tone", tone_options + ["Playful"], index=0, key="flyer_tone")
            if flyer_tone == "Other":
                custom_flyer_tone = st.text_input("Custom tone", key="custom_flyer_tone")
                if custom_flyer_tone:
                    suggestion = fuzzy_correct(custom_flyer_tone, tone_options[1:-1] + ["Playful"])
                    if suggestion != custom_flyer_tone:
                        st.info(f"Did you mean: {suggestion}?")
        
        flyer_context = st.text_input("Flyer Context (optional)", value="", key="flyer_context")
        flyer_cost_mode = st.selectbox("Flyer Cost Mode", ["balanced", "economy", "premium"], key="flyer_cost_mode")
        flyer_image_size = st.selectbox("Flyer Image Size (Aspect Ratio)", ["1024x1024 (Square)", "1792x1024 (Wide)", "1024x1792 (Tall)"], index=0, key="flyer_image_size")
        generate_flyer_btn = st.form_submit_button("Generate Flyer/Banner")

    if generate_flyer_btn:
        with st.spinner("Generating flyer/banner image with advanced prompt engineering..."):
            try:
                final_flyer_category = custom_flyer_category if flyer_category == "Other" and 'custom_flyer_category' in locals() and custom_flyer_category else flyer_category
                final_flyer_event_type = custom_flyer_event_type if flyer_event_type == "Other" and 'custom_flyer_event_type' in locals() and custom_flyer_event_type else flyer_event_type
                final_flyer_tone = custom_flyer_tone if flyer_tone == "Other" and 'custom_flyer_tone' in locals() and custom_flyer_tone else flyer_tone
                
                image_url, flyer_logs = generate_flyer_image(
                    flyer_title if flyer_title else "Event Title",
                    flyer_description if flyer_description else "A professional event.",
                    final_flyer_category if final_flyer_category != "Select event category" else "Business",
                    final_flyer_event_type if final_flyer_event_type != "Select event type" else "Conference",
                    final_flyer_tone if final_flyer_tone != "Select tone of event" else "Professional",
                    flyer_context if flyer_context else None,
                    flyer_cost_mode,
                    flyer_image_size.split()[0]
                )
                st.session_state.flyer_image_url = image_url
                st.session_state.flyer_logs = flyer_logs
            except Exception as e:
                st.error(f"Error generating flyer: {str(e)}")
                st.error("This could be due to API limits or connection issues. Please try again in a few moments.")

    if st.session_state.get("flyer_image_url"):
        st.markdown("### Generated Flyer/Banner:")
        st.image(st.session_state.flyer_image_url, use_container_width=True)
        st.download_button("Download Flyer/Banner", st.session_state.flyer_image_url, file_name="event_flyer.png")
        
        if st.session_state.flyer_logs:
            show_flyer_analytics = st.button("View Flyer/Banner Generation Analytics", key="flyer_analytics_btn")
            if show_flyer_analytics:
                st.markdown("### Flyer/Banner Generation Analytics")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Prompt Tokens", st.session_state.flyer_logs.get('Prompt tokens', 'N/A'))
                    st.metric("Total Tokens", st.session_state.flyer_logs.get('Total tokens', 'N/A'))
                with col2:
                    st.metric("Completion Tokens", st.session_state.flyer_logs.get('Completion tokens', 'N/A'))
                    st.metric("Generation Time", f"{st.session_state.flyer_logs.get('Time taken (s)', 'N/A')}s")
                st.metric("Cost", st.session_state.flyer_logs.get('Estimated cost ($)', 'N/A'))
                st.markdown(f"**Model Used:** {st.session_state.flyer_logs.get('Model', 'dall-e-3')}")
                with st.expander("Show Prompt Preview"):
                    st.markdown(f"""
**Prompt:**
```
{st.session_state.flyer_logs.get('Prompt', '')}
```
""", unsafe_allow_html=True)
        
        st.markdown("### Use This Flyer:")
        st.session_state.final_flyer = st.session_state.flyer_image_url
        st.success("Flyer ready for FAQ generation")

if st.session_state.get("final_title"):
    st.markdown("## FAQs & Refund Policy Generation")
    
    faq_use_same = st.radio(
        "FAQ/Refund Policy Content:",
        ["Use selected title/description/flyer from above", "Enter custom FAQ content"],
        key="faq_use_same",
        help="Choose whether to use the selected content from above or enter custom content for FAQs and refund policy."
    )
    
    with st.form("faq_form", clear_on_submit=False):
        if faq_use_same == "Use selected title/description/flyer from above":
            faq_title = st.text_input("FAQ/Refund Policy Title", value=st.session_state.final_title, key="faq_title_input", disabled=True)
            faq_description = st.text_area("FAQ/Refund Policy Description", value=st.session_state.get("final_description", st.session_state.get("description", "")), key="faq_desc_input", disabled=True)
        else:
            faq_title = st.text_input("FAQ/Refund Policy Title", value=st.session_state.final_title, key="faq_title_input_custom")
            faq_description = st.text_area("FAQ/Refund Policy Description", value=st.session_state.get("final_description", ""), key="faq_desc_input_custom")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            faq_category = st.selectbox("FAQ/Refund Policy Category", category_options, index=0, key="faq_category")
            if faq_category == "Other":
                custom_faq_category = st.text_input("Custom category", key="custom_faq_category")
                if custom_faq_category:
                    suggestion = fuzzy_correct(custom_faq_category, category_options[1:-1])
                    if suggestion != custom_faq_category:
                        st.info(f"Did you mean: {suggestion}?")
        
        with col2:
            faq_event_type = st.selectbox("FAQ/Refund Policy Event Type", event_type_options + ["Gala"], index=0, key="faq_event_type")
            if faq_event_type == "Other":
                custom_faq_event_type = st.text_input("Custom event type", key="custom_faq_event_type")
                if custom_faq_event_type:
                    suggestion = fuzzy_correct(custom_faq_event_type, event_type_options[1:-1])
                    if suggestion != custom_faq_event_type:
                        st.info(f"Did you mean: {suggestion}?")
        
        with col3:
            faq_tone = st.selectbox("FAQ/Refund Policy Tone", tone_options + ["Playful"], index=0, key="faq_tone")
            if faq_tone == "Other":
                custom_faq_tone = st.text_input("Custom tone", key="custom_faq_tone")
                if custom_faq_tone:
                    suggestion = fuzzy_correct(custom_faq_tone, tone_options[1:-1] + ["Playful"])
                    if suggestion != custom_faq_tone:
                        st.info(f"Did you mean: {suggestion}?")
        
        faq_context = st.text_input("FAQ/Refund Policy Context (optional)", value="", key="faq_context")
        faq_cost_mode = st.selectbox("FAQ/Refund Policy Cost Mode", ["balanced", "economy", "premium"], key="faq_cost_mode")
        generate_faq_btn = st.form_submit_button("Generate FAQs & Refund Policy")

    if generate_faq_btn:
        with st.spinner("Generating FAQs and refund policy with advanced prompt engineering..."):
            try:
                final_faq_category = custom_faq_category if faq_category == "Other" and 'custom_faq_category' in locals() and custom_faq_category else faq_category
                final_faq_event_type = custom_faq_event_type if faq_event_type == "Other" and 'custom_faq_event_type' in locals() and custom_faq_event_type else faq_event_type
                final_faq_tone = custom_faq_tone if faq_tone == "Other" and 'custom_faq_tone' in locals() and custom_faq_tone else faq_tone
                
                faqs, refund_policy, faq_logs = generate_faqs_and_refund_policy(
                    faq_title if faq_title else "Event Title",
                    faq_description if faq_description else "A professional event.",
                    final_faq_category if final_faq_category != "Select event category" else "Business",
                    final_faq_event_type if final_faq_event_type != "Select event type" else "Conference",
                    final_faq_tone if final_faq_tone != "Select tone of event" else "Professional",
                    faq_context if faq_context else None,
                    faq_cost_mode
                )
                st.session_state.faqs = faqs
                st.session_state.refund_policy = refund_policy
                st.session_state.faq_logs = faq_logs
            except Exception as e:
                st.error(f"Error generating FAQs/refund policy: {str(e)}")
                st.error("Please try again or check your API key.")

    if st.session_state.get("faqs"):
        st.markdown("### Generated FAQs:")
        for i, faq in enumerate(st.session_state.faqs, 1):
            with st.expander(f"Q{i}: {faq['question']}"):
                st.markdown(f"**A:** {faq['answer']}")
        st.download_button("Download FAQs", "\n\n".join([f"Q: {f['question']}\nA: {f['answer']}" for f in st.session_state.faqs]), file_name="event_faqs.txt", mime="text/plain", key="download_faqs_btn")
        
        st.markdown("### Customize Your FAQs:")
        faq_options = ["Use generated FAQs as-is", "Edit generated FAQs", "Add my own FAQs", "Mix generated and custom FAQs"]
        faq_choice = st.selectbox("Choose how you want to proceed with FAQs:", faq_options, key="faq_choice")
        
        if faq_choice == "Use generated FAQs as-is":
            st.session_state.final_faqs = st.session_state.faqs
            st.success(f"Using {len(st.session_state.faqs)} generated FAQs")
        
        elif faq_choice == "Edit generated FAQs":
            st.markdown("#### Edit Generated FAQs:")
            edited_faqs = []
            for i, faq in enumerate(st.session_state.faqs):
                st.markdown(f"**FAQ {i+1}:**")
                edited_question = st.text_input(f"Question {i+1}:", value=faq['question'], key=f"edit_faq_q_{i}")
                edited_answer = st.text_area(f"Answer {i+1}:", value=faq['answer'], key=f"edit_faq_a_{i}", height=100)
                if edited_question and edited_answer:
                    edited_faqs.append({"question": edited_question, "answer": edited_answer})
            if edited_faqs:
                st.session_state.final_faqs = edited_faqs
                st.success(f"Using {len(edited_faqs)} edited FAQs")
        
        elif faq_choice == "Add my own FAQs":
            st.markdown("#### Add Your Own FAQs:")
            num_custom_faqs = st.slider("Number of custom FAQs to add:", min_value=1, max_value=10, value=5)
            custom_faqs = []
            for i in range(num_custom_faqs):
                st.markdown(f"**Custom FAQ {i+1}:**")
                custom_question = st.text_input(f"Custom Question {i+1}:", key=f"custom_faq_q_{i}")
                custom_answer = st.text_area(f"Custom Answer {i+1}:", key=f"custom_faq_a_{i}", height=100)
                if custom_question and custom_answer:
                    custom_faqs.append({"question": custom_question, "answer": custom_answer})
            if custom_faqs:
                st.session_state.final_faqs = custom_faqs
                st.success(f"Using {len(custom_faqs)} custom FAQs")
        
        elif faq_choice == "Mix generated and custom FAQs":
            st.markdown("#### Select Generated FAQs to Keep:")
            selected_generated = []
            for i, faq in enumerate(st.session_state.faqs):
                keep_faq = st.checkbox(f"Keep: {faq['question']}", key=f"keep_faq_{i}")
                if keep_faq:
                    selected_generated.append(faq)
            
            st.markdown("#### Add Additional Custom FAQs:")
            num_additional = st.slider("Number of additional custom FAQs:", min_value=0, max_value=10, value=2)
            additional_faqs = []
            for i in range(num_additional):
                st.markdown(f"**Additional FAQ {i+1}:**")
                add_question = st.text_input(f"Additional Question {i+1}:", key=f"add_faq_q_{i}")
                add_answer = st.text_area(f"Additional Answer {i+1}:", key=f"add_faq_a_{i}", height=100)
                if add_question and add_answer:
                    additional_faqs.append({"question": add_question, "answer": add_answer})
            
            mixed_faqs = selected_generated + additional_faqs
            if mixed_faqs:
                st.session_state.final_faqs = mixed_faqs
                st.success(f"Using {len(selected_generated)} generated + {len(additional_faqs)} custom FAQs = {len(mixed_faqs)} total FAQs")

    if st.session_state.get("refund_policy"):
        st.markdown("### Generated Refund Policy:")
        st.markdown(f'<div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #2563eb; color: #333;">{st.session_state.refund_policy}</div>', unsafe_allow_html=True)
        st.download_button("Download Refund Policy", st.session_state.refund_policy, file_name="event_refund_policy.txt", mime="text/plain", key="download_refund_btn")
        
        st.markdown("### Customize Refund Policy:")
        refund_options = ["Use generated refund policy", "Edit refund policy", "Write my own refund policy"]
        refund_choice = st.selectbox("Choose how you want to proceed with refund policy:", refund_options, key="refund_choice")
        
        if refund_choice == "Use generated refund policy":
            st.session_state.final_refund_policy = st.session_state.refund_policy
            st.success("Using generated refund policy")
        elif refund_choice == "Edit refund policy":
            edited_refund = st.text_area("Edit the refund policy:", 
                                       value=st.session_state.refund_policy, 
                                       key="edit_refund", height=150)
            if edited_refund:
                st.session_state.final_refund_policy = edited_refund
                st.success("Using edited refund policy")
        else:
            custom_refund = st.text_area("Write your own refund policy:", 
                                       placeholder="Enter your custom refund policy...", 
                                       key="custom_refund", height=150)
            if custom_refund:
                st.session_state.final_refund_policy = custom_refund
                st.success("Using custom refund policy")
        
        if st.session_state.faq_logs:
            show_faq_analytics = st.button("View FAQ/Refund Generation Analytics", key="faq_analytics_btn")
            if show_faq_analytics:
                st.markdown("### FAQ/Refund Generation Analytics")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Prompt Tokens", st.session_state.faq_logs.get('Prompt tokens', 'N/A'))
                    st.metric("Total Tokens", st.session_state.faq_logs.get('Total tokens', 'N/A'))
                with col2:
                    st.metric("Completion Tokens", st.session_state.faq_logs.get('Completion tokens', 'N/A'))
                    st.metric("Generation Time", f"{st.session_state.faq_logs.get('Time taken (s)', 'N/A')}s")
                st.metric("Cost", st.session_state.faq_logs.get('Estimated cost ($)', 'N/A'))
                st.markdown(f"**Model Used:** {st.session_state.faq_logs.get('Model', 'gpt-3.5-turbo')}")
                with st.expander("Show Prompt Preview"):
                    st.markdown(f"""
**System Prompt:**
```
{st.session_state.faq_logs.get('System prompt', '')}
```
**User Prompt:**
```
{st.session_state.faq_logs.get('Prompt', '')}
```
""", unsafe_allow_html=True)

content_complete = (
    st.session_state.get("final_title") and 
    st.session_state.get("final_description") and 
    st.session_state.get("final_flyer") and 
    st.session_state.get("final_faqs") and 
    st.session_state.get("final_refund_policy")
)

if content_complete:
    st.markdown("---")
    st.markdown("## Complete Event Package")
    
    show_event_summary = st.button("Show Complete Event Summary", key="show_event_summary_btn")
    
    if show_event_summary:
        st.markdown("---")
        
        st.markdown("# EVENT SUMMARY")
        st.markdown("---")
        
        st.markdown("## TITLE")
        st.markdown(f"**{st.session_state.final_title}**")
        st.markdown("---")
        
        st.markdown("## DESCRIPTION")
        st.markdown(st.session_state.final_description)
        st.markdown("---")
        
        st.markdown("## EVENT FLYER")
        st.image(st.session_state.final_flyer, use_container_width=True)
        st.markdown("---")
        
        st.markdown("## FREQUENTLY ASKED QUESTIONS")
        for i, faq in enumerate(st.session_state.final_faqs, 1):
            st.markdown(f"**• Q{i}: {faq['question']}**")
            st.markdown(f"  **Answer:** {faq['answer']}")
            st.markdown("")
        st.markdown("---")
        
        st.markdown("## REFUND POLICY")
        policy_lines = st.session_state.final_refund_policy.split('. ')
        for line in policy_lines:
            if line.strip():
                clean_line = line.strip().rstrip('.')
                if clean_line:
                    st.markdown(f"• {clean_line}")
        
        st.markdown("---")
        
        summary_text = f"""EVENT SUMMARY

TITLE:
{st.session_state.final_title}

DESCRIPTION:
{st.session_state.final_description}

FREQUENTLY ASKED QUESTIONS:
{chr(10).join([f"• Q{i}: {faq['question']}{chr(10)}  Answer: {faq['answer']}{chr(10)}" for i, faq in enumerate(st.session_state.final_faqs, 1)])}

REFUND POLICY:
{chr(10).join([f"• {line.strip().rstrip('.')}" for line in st.session_state.final_refund_policy.split('.') if line.strip()])}

FLYER URL:
{st.session_state.final_flyer}
"""
        
        st.download_button(
            "Download Complete Event Summary", 
            summary_text, 
            file_name="complete_event_summary.txt", 
            mime="text/plain", 
            key="download_complete_summary_btn"
        )

st.markdown("---")
st.markdown("**Ready for Flask integration:** This system supports sequential content generation with user selection at each step.")