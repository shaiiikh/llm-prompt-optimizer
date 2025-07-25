import streamlit as st
import os

try:
    from event_llm_core import generate_titles, generate_description, generate_flyer_image, generate_banner_image, generate_faqs, generate_refund_policy, fuzzy_correct, get_global_analytics, reset_analytics
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
.description-box {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 8px;
    border-left: 4px solid #28a745;
    color: #333;
    line-height: 1.6;
    margin: 1rem 0;
}
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
        ("Technology", "Conference", "Professional"): "Technology conferences perform best with titles that emphasize innovation, future trends, and networking opportunities.",
        ("Technology", "Workshop", "Creative"): "Creative technology workshops work best when titles suggest hands-on learning and innovation.",
        ("Business", "Workshop", "Formal"): "Formal business workshops should highlight specific skills, ROI, and executive-level insights.",
        ("Business", "Conference", "Professional"): "Professional business conferences perform best with titles emphasizing leadership and strategic outcomes.",
        ("Education", "Seminar", "Creative"): "Creative education seminars work best when titles suggest transformation and hands-on learning.",
        ("Education", "Conference", "Innovative"): "Innovative education conferences should emphasize future learning methods and technology integration.",
        ("Health", "Workshop", "Friendly"): "Friendly health workshops perform best with approachable titles that emphasize wellness and community.",
        ("Entertainment", "Festival", "Casual"): "Casual entertainment festivals work best with energetic titles that create excitement.",
        ("Sports", "Conference", "Professional"): "Professional sports conferences should emphasize performance, strategy, and industry insights.",
        ("Arts & Culture", "Exhibition", "Creative"): "Creative arts exhibitions work best with inspiring titles that evoke curiosity and artistic expression."
    }
    
    key = (category, event_type, tone)
    if key in tips:
        return tips[key]
    
    return f"{tone} {event_type}s in {category} perform best when titles clearly communicate the unique value and target outcome."

def suggest_optimal_settings(category, event_type):
    suggestions = {
        ("Technology", "Conference"): {"tone": "Professional", "titles": 5, "desc_length": 1200},
        ("Technology", "Workshop"): {"tone": "Creative", "titles": 4, "desc_length": 800},
        ("Technology", "Seminar"): {"tone": "Professional", "titles": 4, "desc_length": 1000},
        ("Technology", "Webinar"): {"tone": "Innovative", "titles": 4, "desc_length": 900},
        ("Technology", "Festival"): {"tone": "Creative", "titles": 5, "desc_length": 1100},
        ("Technology", "Exhibition"): {"tone": "Professional", "titles": 4, "desc_length": 1000},
        ("Business", "Conference"): {"tone": "Professional", "titles": 5, "desc_length": 1400},
        ("Business", "Workshop"): {"tone": "Formal", "titles": 4, "desc_length": 900},
        ("Business", "Seminar"): {"tone": "Formal", "titles": 3, "desc_length": 1000},
        ("Business", "Webinar"): {"tone": "Professional", "titles": 4, "desc_length": 1000},
        ("Business", "Festival"): {"tone": "Professional", "titles": 4, "desc_length": 1200},
        ("Business", "Exhibition"): {"tone": "Professional", "titles": 4, "desc_length": 1100},
        ("Education", "Conference"): {"tone": "Innovative", "titles": 5, "desc_length": 1400},
        ("Education", "Workshop"): {"tone": "Creative", "titles": 4, "desc_length": 900},
        ("Education", "Seminar"): {"tone": "Innovative", "titles": 4, "desc_length": 1100},
        ("Education", "Webinar"): {"tone": "Creative", "titles": 5, "desc_length": 1000},
        ("Education", "Festival"): {"tone": "Creative", "titles": 5, "desc_length": 1200},
        ("Education", "Exhibition"): {"tone": "Innovative", "titles": 4, "desc_length": 1000},
        ("Health", "Conference"): {"tone": "Professional", "titles": 4, "desc_length": 1300},
        ("Health", "Workshop"): {"tone": "Friendly", "titles": 4, "desc_length": 900},
        ("Health", "Seminar"): {"tone": "Professional", "titles": 3, "desc_length": 800},
        ("Health", "Webinar"): {"tone": "Friendly", "titles": 4, "desc_length": 900},
        ("Health", "Festival"): {"tone": "Friendly", "titles": 5, "desc_length": 1100},
        ("Health", "Exhibition"): {"tone": "Professional", "titles": 4, "desc_length": 1000},
        ("Entertainment", "Conference"): {"tone": "Creative", "titles": 4, "desc_length": 1100},
        ("Entertainment", "Workshop"): {"tone": "Casual", "titles": 4, "desc_length": 800},
        ("Entertainment", "Seminar"): {"tone": "Creative", "titles": 3, "desc_length": 900},
        ("Entertainment", "Webinar"): {"tone": "Casual", "titles": 4, "desc_length": 800},
        ("Entertainment", "Festival"): {"tone": "Casual", "titles": 5, "desc_length": 1000},
        ("Entertainment", "Exhibition"): {"tone": "Creative", "titles": 5, "desc_length": 1100},
        ("Sports", "Conference"): {"tone": "Professional", "titles": 4, "desc_length": 1200},
        ("Sports", "Workshop"): {"tone": "Professional", "titles": 4, "desc_length": 900},
        ("Sports", "Seminar"): {"tone": "Professional", "titles": 3, "desc_length": 800},
        ("Sports", "Webinar"): {"tone": "Professional", "titles": 4, "desc_length": 900},
        ("Sports", "Festival"): {"tone": "Casual", "titles": 5, "desc_length": 1100},
        ("Sports", "Exhibition"): {"tone": "Professional", "titles": 4, "desc_length": 1000},
        ("Arts & Culture", "Conference"): {"tone": "Creative", "titles": 4, "desc_length": 1200},
        ("Arts & Culture", "Workshop"): {"tone": "Creative", "titles": 4, "desc_length": 900},
        ("Arts & Culture", "Seminar"): {"tone": "Creative", "titles": 3, "desc_length": 900},
        ("Arts & Culture", "Webinar"): {"tone": "Creative", "titles": 4, "desc_length": 800},
        ("Arts & Culture", "Festival"): {"tone": "Creative", "titles": 5, "desc_length": 1200},
        ("Arts & Culture", "Exhibition"): {"tone": "Creative", "titles": 5, "desc_length": 1100}
    }
    
    key = (category, event_type)
    return suggestions.get(key, {"tone": "Professional", "titles": 3, "desc_length": 800})

def get_combined_context():
    if not st.session_state.master_context and not st.session_state.context_updates:
        return None
    
    combined = st.session_state.master_context
    if st.session_state.context_updates:
        combined += " " + " ".join(st.session_state.context_updates)
    
    return combined.strip() if combined.strip() else None

def add_context_update(new_info):
    if new_info and new_info.strip():
        st.session_state.context_updates.append(new_info.strip())

def display_current_context():
    context = get_combined_context()
    if context:
        st.info(f"**Current Context:** {context}")
    else:
        st.info("**Current Context:** None")

def validate_form_inputs(category, event_type, tone, required_fields=None):
    errors = []
    
    if category == "Select event category":
        errors.append("Please select an event category")
    
    if event_type == "Select event type":
        errors.append("Please select an event type")
    
    if tone == "Select tone of event":
        errors.append("Please select a tone for your event")
    
    if required_fields:
        for field_name, field_value in required_fields.items():
            if not field_value or field_value.strip() == "":
                errors.append(f"Please provide {field_name}")
    
    return errors

def show_validation_errors(errors):
    if errors:
        for error in errors:
            st.warning(f"{error}")
        return True
    return False

def show_context_input(step_name, key_suffix=""):
    st.markdown(f"### Add More Context for {step_name}")
    st.markdown("You can add more information or changes that will be used for all future generations:")
    
    new_context = st.text_area(
        f"Additional context or changes for {step_name}:",
        placeholder=f"e.g., Make it more focused on sustainability, Add networking aspects, Change the target audience to executives...",
        key=f"new_context_{key_suffix}",
        help="This will be combined with your previous context and used for all future content generation."
    )
    
    if st.button(f"Add Context for {step_name}", key=f"add_context_{key_suffix}"):
        if new_context:
            add_context_update(new_context)
            st.success(f"Added context: {new_context}")
            st.rerun()
        else:
            st.warning("Please enter some context to add.")
    
    return new_context

def initialize_session_state():
    session_vars = {
        'generated_titles': [],
        'final_title': "",
        'description': "",
        'final_description': "",
        'flyer_image_url': "",
        'final_flyer': "",
        'faqs': [],
        'final_faqs': [],
        'refund_policy': "",
        'final_refund_policy': "",
        'title_logs': None,
        'desc_logs': None,
        'flyer_logs': None,
        'faq_logs': None,
        'refund_logs': None,
        'master_context': "",
        'context_updates': []
    }
    
    for var, default_value in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default_value

initialize_session_state()

CATEGORY_OPTIONS = ["Select event category", "Technology", "Business", "Education", "Health", "Entertainment", "Sports", "Arts & Culture", "Other"]
EVENT_TYPE_OPTIONS = ["Select event type", "Conference", "Workshop", "Seminar", "Webinar", "Festival", "Exhibition", "Meetup", "Other"]
TONE_OPTIONS = ["Select tone of event", "Professional", "Casual", "Formal", "Creative", "Premium", "Innovative", "Friendly", "Corporate", "Other"]

st.markdown("## Title Generation")

col1, col2, col3 = st.columns(3)

with col1:
    title_category = st.selectbox("Category for Titles", CATEGORY_OPTIONS, index=1, key="title_category")
    if title_category == "Other":
        custom_title_category = st.text_input("Custom category", key="custom_title_category")
        if custom_title_category:
            suggestion = fuzzy_correct(custom_title_category, CATEGORY_OPTIONS[1:-1])
            if suggestion != custom_title_category:
                st.info(f"Did you mean: {suggestion}?")

with col2:
    title_event_type = st.selectbox("Event Type for Titles", EVENT_TYPE_OPTIONS, index=1, key="title_event_type")
    if title_event_type == "Other":
        custom_title_event_type = st.text_input("Custom event type", key="custom_title_event_type")
        if custom_title_event_type:
            suggestion = fuzzy_correct(custom_title_event_type, EVENT_TYPE_OPTIONS[1:-1])
            if suggestion != custom_title_event_type:
                st.info(f"Did you mean: {suggestion}?")

with col3:
    title_tone = st.selectbox("Tone for Titles", TONE_OPTIONS, index=1, key="title_tone")
    if title_tone == "Other":
        custom_title_tone = st.text_input("Custom tone", key="custom_title_tone")
        if custom_title_tone:
            suggestion = fuzzy_correct(custom_title_tone, TONE_OPTIONS[1:-1])
            if suggestion != custom_title_tone:
                st.info(f"Did you mean: {suggestion}?")

if title_category != "Select event category" and title_event_type != "Select event type":
    optimal = suggest_optimal_settings(title_category, title_event_type)
    st.markdown(f'<div class="optimization-tip">Optimization Suggestion: For {title_category} {title_event_type}s, recommended settings are {optimal["tone"]} tone with {optimal["titles"]} titles.</div>', unsafe_allow_html=True)

if title_category != "Select event category" and title_event_type != "Select event type" and title_tone != "Select tone of event":
    tip = get_optimization_tip(title_category, title_event_type, title_tone)
    st.info(tip)

with st.form("title_form", clear_on_submit=False):
    cost_mode = st.selectbox("Cost Optimization", ["balanced", "economy", "premium"], key="cost_mode")
    num_titles = st.slider("Number of Titles (max 5)", min_value=1, max_value=5, value=3)
    title_context = st.text_input("Context for Titles (optional)", placeholder="e.g., Focus on AI and machine learning trends")
    generate_titles_btn = st.form_submit_button("Generate Titles")

if generate_titles_btn:
    final_category = custom_title_category if title_category == "Other" and custom_title_category else title_category
    final_event_type = custom_title_event_type if title_event_type == "Other" and custom_title_event_type else title_event_type
    final_tone = custom_title_tone if title_tone == "Other" and custom_title_tone else title_tone
    
    validation_errors = validate_form_inputs(final_category, final_event_type, final_tone)
    
    if show_validation_errors(validation_errors):
        st.stop()
    
    if title_context and not st.session_state.master_context:
        st.session_state.master_context = title_context
    
    with st.spinner("Generating titles with advanced prompt engineering..."):
        try:
            combined_context = get_combined_context()
            
            titles, logs = generate_titles(
                final_category,
                final_event_type,
                final_tone,
                num_titles,
                combined_context,
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
    
    display_current_context()
    show_context_input("Title Generation", "titles")
    
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
            desc_context = st.text_input("Context for Description (optional)", value=get_combined_context() or "", key="desc_context", disabled=True)
            desc_cost_mode = st.selectbox("Description Cost Mode", ["balanced", "economy", "premium"], index=["balanced", "economy", "premium"].index(cost_mode), key="desc_cost_mode", disabled=True)
        else:
            desc_title = st.text_input("Title for Description", value=st.session_state.final_title, key="desc_title_input_custom")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                desc_category = st.selectbox("Category for Description", CATEGORY_OPTIONS, index=1, key="desc_category_custom")
                if desc_category == "Other":
                    custom_desc_category = st.text_input("Custom category", key="custom_desc_category")
                    if custom_desc_category:
                        suggestion = fuzzy_correct(custom_desc_category, CATEGORY_OPTIONS[1:-1])
                        if suggestion != custom_desc_category:
                            st.info(f"Did you mean: {suggestion}?")
            
            with col2:
                desc_event_type = st.selectbox("Event Type for Description", EVENT_TYPE_OPTIONS, index=1, key="desc_event_type_custom")
                if desc_event_type == "Other":
                    custom_desc_event_type = st.text_input("Custom event type", key="custom_desc_event_type")
                    if custom_desc_event_type:
                        suggestion = fuzzy_correct(custom_desc_event_type, EVENT_TYPE_OPTIONS[1:-1])
                        if suggestion != custom_desc_event_type:
                            st.info(f"Did you mean: {suggestion}?")
            
            with col3:
                desc_tone = st.selectbox("Tone for Description", TONE_OPTIONS, index=1, key="desc_tone_custom")
                if desc_tone == "Other":
                    custom_desc_tone = st.text_input("Custom tone", key="custom_desc_tone")
                    if custom_desc_tone:
                        suggestion = fuzzy_correct(custom_desc_tone, TONE_OPTIONS[1:-1])
                        if suggestion != custom_desc_tone:
                            st.info(f"Did you mean: {suggestion}?")
            
            desc_context = st.text_input("Context for Description (optional)", value="", key="desc_context_custom")
            desc_cost_mode = st.selectbox("Description Cost Mode", ["balanced", "economy", "premium"], key="desc_cost_mode_custom")
        
        max_chars = st.slider("Description Length (characters)", min_value=100, max_value=5000, value=800)
        generate_desc_btn = st.form_submit_button("Generate Description")

    if generate_desc_btn:
        if desc_use_same != "Use same title and settings as above":
            final_desc_category = custom_desc_category if desc_category == "Other" and custom_desc_category else desc_category
            final_desc_event_type = custom_desc_event_type if desc_event_type == "Other" and custom_desc_event_type else desc_event_type
            final_desc_tone = custom_desc_tone if desc_tone == "Other" and custom_desc_tone else desc_tone
        else:
            final_desc_category = desc_category
            final_desc_event_type = desc_event_type
            final_desc_tone = desc_tone
        
        with st.spinner("Generating description with advanced prompt engineering..."):
            try:
                combined_context = get_combined_context()
                
                description, logs = generate_description(
                    desc_title,
                    final_desc_category,
                    final_desc_event_type,
                    final_desc_tone,
                    combined_context,
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
        st.markdown(f'<div class="description-box">{st.session_state.description}</div>', unsafe_allow_html=True)
        st.info(f"Description length: {len(st.session_state.description)} characters")
        st.download_button("Download as .txt", st.session_state.description, file_name="event_description.txt", mime="text/plain", key="download_desc_btn")
        
        display_current_context()
        show_context_input("Description Generation", "description")
        
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
    st.markdown("## Visual Content Generation")
    
    visual_type = st.radio(
        "Choose Visual Type:",
        ["Flyer (Portrait/Vertical - Detailed Information)", "Banner (Landscape/Horizontal - Digital Display)"],
        key="visual_type",
        help="Flyers are portrait-oriented with detailed event information. Banners are landscape-oriented for digital displays with minimal text."
    )
    
    content_use_same = st.radio(
        "Content Source:",
        ["Use selected title/description from above", "Enter custom content"],
        key="content_use_same",
        help="Choose whether to use the selected title and description or enter custom content."
    )
    
    with st.form("visual_generation_form", clear_on_submit=False):
        if content_use_same == "Use selected title/description from above":
            visual_title = st.text_input(f"{'Flyer' if 'Flyer' in visual_type else 'Banner'} Title", value=st.session_state.final_title, key="visual_title_input", disabled=True)
            visual_description = st.text_area(f"{'Flyer' if 'Flyer' in visual_type else 'Banner'} Description", value=st.session_state.get("final_description", st.session_state.get("description", "")), key="visual_desc_input", disabled=True)
        else:
            visual_title = st.text_input(f"{'Flyer' if 'Flyer' in visual_type else 'Banner'} Title", value=st.session_state.final_title, key="visual_title_input_custom")
            visual_description = st.text_area(f"{'Flyer' if 'Flyer' in visual_type else 'Banner'} Description", value=st.session_state.get("final_description", ""), key="visual_desc_input_custom")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            visual_category = st.selectbox(f"{'Flyer' if 'Flyer' in visual_type else 'Banner'} Category", CATEGORY_OPTIONS, index=1, key="visual_category")
            if visual_category == "Other":
                custom_visual_category = st.text_input("Custom category", key="custom_visual_category")
        
        with col2:
            visual_event_type = st.selectbox(f"{'Flyer' if 'Flyer' in visual_type else 'Banner'} Event Type", EVENT_TYPE_OPTIONS + ["Gala"], index=1, key="visual_event_type")
            if visual_event_type == "Other":
                custom_visual_event_type = st.text_input("Custom event type", key="custom_visual_event_type")
        
        with col3:
            visual_tone = st.selectbox(f"{'Flyer' if 'Flyer' in visual_type else 'Banner'} Tone", TONE_OPTIONS + ["Playful"], index=1, key="visual_tone")
            if visual_tone == "Other":
                custom_visual_tone = st.text_input("Custom tone", key="custom_visual_tone")
        
        st.markdown("**Event Details:**")
        col1, col2 = st.columns(2)
        with col1:
            event_date = st.text_input("Date", placeholder="e.g., July 27, 2024", key="event_date")
            event_location = st.text_input("Location/Venue", placeholder="e.g., Karachi, Pakistan", key="event_location")
        with col2:
            event_time = st.text_input("Time", placeholder="e.g., 2:00 PM", key="event_time")
            event_speaker = st.text_input("Speaker(s)", placeholder="e.g., Ali Shaikh", key="event_speaker")
        
        event_format = st.selectbox("Event Format", ["Online", "Offline/In-person", "Hybrid"], key="event_format")
        
        visual_context = st.text_area(
            f"Additional Context (Optional)",
            value=get_combined_context() or "",
            key="visual_context",
            placeholder="Any additional details about the event...",
            help="Optional field for extra event information"
        )
        visual_cost_mode = st.selectbox(f"{'Flyer' if 'Flyer' in visual_type else 'Banner'} Cost Mode", ["balanced", "economy", "premium"], key="visual_cost_mode")
        
        if "Flyer" in visual_type:
            visual_image_size = st.selectbox("Flyer Image Size", ["1024x1792 (Portrait)", "1024x1024 (Square)"], index=0, key="visual_image_size")
        else:
            visual_image_size = st.selectbox("Banner Image Size", ["1792x1024 (Landscape)", "1024x1024 (Square)"], index=0, key="visual_image_size")
        
        generate_visual_btn = st.form_submit_button(f"Generate {'Flyer' if 'Flyer' in visual_type else 'Banner'}")

    if generate_visual_btn:
        final_visual_category = custom_visual_category if visual_category == "Other" and custom_visual_category else visual_category
        final_visual_event_type = custom_visual_event_type if visual_event_type == "Other" and custom_visual_event_type else visual_event_type
        final_visual_tone = custom_visual_tone if visual_tone == "Other" and custom_visual_tone else visual_tone
        
        if not visual_description or visual_description.strip() == "":
            visual_description = f"A {final_visual_tone.lower()} {final_visual_category.lower()} {final_visual_event_type.lower()} event"
        
        visual_type_name = "flyer" if "Flyer" in visual_type else "banner"
        
        with st.spinner(f"Generating {visual_type_name} with advanced prompt engineering..."):
            try:
                structured_context = []
                if event_date and event_date.strip():
                    structured_context.append(f"Date: {event_date.strip()}")
                if event_time and event_time.strip():
                    structured_context.append(f"Time: {event_time.strip()}")
                if event_speaker and event_speaker.strip():
                    structured_context.append(f"Speaker: {event_speaker.strip()}")
                if event_location and event_location.strip():
                    structured_context.append(f"Location: {event_location.strip()}")
                if event_format and event_format != "Select...":
                    structured_context.append(f"Format: {event_format}")
                
                base_context = " | ".join(structured_context) if structured_context else ""
                additional_context = visual_context.strip() if visual_context else get_combined_context() or ""
                combined_context = f"{base_context} | {additional_context}".strip(" |") if additional_context else base_context
                
                if "Flyer" in visual_type:
                    image_url, visual_logs = generate_flyer_image(
                        visual_title,
                        visual_description,
                        final_visual_category,
                        final_visual_event_type,
                        final_visual_tone,
                        combined_context,
                        visual_cost_mode,
                        visual_image_size.split()[0]
                    )
                else:
                    image_url, visual_logs = generate_banner_image(
                        visual_title,
                        visual_description,
                        final_visual_category,
                        final_visual_event_type,
                        final_visual_tone,
                        combined_context,
                        visual_cost_mode,
                        visual_image_size.split()[0]
                    )
                
                if image_url and (isinstance(image_url, bytes) and len(image_url) > 0) or (isinstance(image_url, str) and image_url.strip()):
                    st.session_state.flyer_image_url = image_url
                    st.session_state.flyer_logs = visual_logs
                    st.session_state.visual_type_generated = visual_type_name
                    st.success(f"Successfully generated {visual_type_name.title()}!")
                else:
                    st.error(f"Failed to generate {visual_type_name}. Please try again.")
                
            except Exception as e:
                st.error(f"Error generating {visual_type_name}: {str(e)}")
                st.error("Please try again or check your API key.")

    image_data = st.session_state.get("flyer_image_url")
    visual_type_display = st.session_state.get("visual_type_generated", "visual").title()
    
    if image_data is not None and (isinstance(image_data, bytes) and len(image_data) > 0) or (isinstance(image_data, str) and image_data.strip()):
        st.markdown(f"### Generated {visual_type_display}:")
        
        if isinstance(image_data, bytes):
            import io
            image_buffer = io.BytesIO(image_data)
            st.image(image_buffer, use_container_width=True)
            st.download_button(f"Download {visual_type_display}", image_data, file_name=f"event_{st.session_state.get('visual_type_generated', 'visual')}.png", mime="image/png")
        else:
            st.image(image_data, use_container_width=True)
            st.download_button(f"Download {visual_type_display}", image_data, file_name=f"event_{st.session_state.get('visual_type_generated', 'visual')}.png")
        
        display_current_context()
        show_context_input(f"{visual_type_display} Generation", st.session_state.get('visual_type_generated', 'visual'))
        
        if st.session_state.flyer_logs:
            show_flyer_analytics = st.button(f"View {visual_type_display} Generation Analytics", key="flyer_analytics_btn")
            if show_flyer_analytics:
                st.markdown(f"### {visual_type_display} Generation Analytics")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Prompt Tokens", st.session_state.flyer_logs.get('Prompt tokens', 'N/A'))
                    st.metric("Total Tokens", st.session_state.flyer_logs.get('Total tokens', 'N/A'))
                with col2:
                    st.metric("Completion Tokens", st.session_state.flyer_logs.get('Completion tokens', 'N/A'))
                    st.metric("Generation Time", f"{st.session_state.flyer_logs.get('Time taken (s)', 'N/A')}s")
                st.metric("Cost", st.session_state.flyer_logs.get('Estimated cost ($)', 'N/A'))
                st.markdown(f"**Model Used:** {st.session_state.flyer_logs.get('Model', 'dall-e-3')}")
                
        st.markdown(f"### Use This {visual_type_display}:")
        st.session_state.final_flyer = st.session_state.flyer_image_url
        st.success(f"{visual_type_display} ready for FAQ generation")

if st.session_state.get("final_title"):
    st.markdown("## FAQs Generation")
    
    faq_use_same = st.radio(
        "FAQ Content:",
        ["Use selected title/description from above", "Enter custom FAQ content"],
        key="faq_use_same",
        help="Choose whether to use the selected content from above or enter custom content for FAQs."
    )
    
    with st.form("faq_form", clear_on_submit=False):
        if faq_use_same == "Use selected title/description from above":
            faq_title = st.text_input("FAQ Title", value=st.session_state.final_title, key="faq_title_input", disabled=True)
            faq_description = st.text_area("FAQ Description", value=st.session_state.get("final_description", st.session_state.get("description", "")), key="faq_desc_input", disabled=True)
        else:
            faq_title = st.text_input("FAQ Title", value=st.session_state.final_title, key="faq_title_input_custom")
            faq_description = st.text_area("FAQ Description", value=st.session_state.get("final_description", ""), key="faq_desc_input_custom")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            faq_category = st.selectbox("FAQ Category", CATEGORY_OPTIONS, index=1, key="faq_category")
            if faq_category == "Other":
                custom_faq_category = st.text_input("Custom category", key="custom_faq_category")
        
        with col2:
            faq_event_type = st.selectbox("FAQ Event Type", EVENT_TYPE_OPTIONS + ["Gala"], index=1, key="faq_event_type")
            if faq_event_type == "Other":
                custom_faq_event_type = st.text_input("Custom event type", key="custom_faq_event_type")
        
        with col3:
            faq_tone = st.selectbox("FAQ Tone", TONE_OPTIONS + ["Playful"], index=1, key="faq_tone")
            if faq_tone == "Other":
                custom_faq_tone = st.text_input("Custom tone", key="custom_faq_tone")
        
        faq_context = st.text_input("FAQ Context (optional)", value=get_combined_context() or "", key="faq_context")
        faq_cost_mode = st.selectbox("FAQ Cost Mode", ["balanced", "economy", "premium"], key="faq_cost_mode")
        generate_faq_btn = st.form_submit_button("Generate FAQs")

    if generate_faq_btn:
        final_faq_category = custom_faq_category if faq_category == "Other" and custom_faq_category else faq_category
        final_faq_event_type = custom_faq_event_type if faq_event_type == "Other" and custom_faq_event_type else faq_event_type
        final_faq_tone = custom_faq_tone if faq_tone == "Other" and custom_faq_tone else faq_tone
        
        if not faq_description or faq_description.strip() == "":
            faq_description = f"A {final_faq_tone.lower()} {final_faq_category.lower()} {final_faq_event_type.lower()} event"
        
        with st.spinner("Generating FAQs with advanced prompt engineering..."):
            try:
                combined_context = get_combined_context()
                
                faqs, faq_logs = generate_faqs(
                    faq_title,
                    faq_description,
                    final_faq_category,
                    final_faq_event_type,
                    final_faq_tone,
                    combined_context,
                    faq_cost_mode
                )
                st.session_state.faqs = faqs
                st.session_state.faq_logs = faq_logs
            except Exception as e:
                st.error(f"Error generating FAQs: {str(e)}")
                st.error("Please try again or check your API key.")

    if st.session_state.get("faqs"):
        st.markdown("### Generated FAQs:")
        for i, faq in enumerate(st.session_state.faqs, 1):
            with st.expander(f"Q{i}: {faq['question']}"):
                st.markdown(f"**A:** {faq['answer']}")
        st.download_button("Download FAQs", "\n\n".join([f"Q: {f['question']}\nA: {f['answer']}" for f in st.session_state.faqs]), file_name="event_faqs.txt", mime="text/plain", key="download_faqs_btn")
        
        display_current_context()
        show_context_input("FAQ Generation", "faq")
        
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

if st.session_state.get("final_title"):
    st.markdown("## Refund Policy Generation")
    
    refund_use_same = st.radio(
        "Refund Policy Content:",
        ["Use selected title/description from above", "Enter custom refund policy content"],
        key="refund_use_same",
        help="Choose whether to use the selected content from above or enter custom content for refund policy."
    )
    
    with st.form("refund_form", clear_on_submit=False):
        if refund_use_same == "Use selected title/description from above":
            refund_title = st.text_input("Refund Policy Title", value=st.session_state.final_title, key="refund_title_input", disabled=True)
            refund_description = st.text_area("Refund Policy Description", value=st.session_state.get("final_description", st.session_state.get("description", "")), key="refund_desc_input", disabled=True)
        else:
            refund_title = st.text_input("Refund Policy Title", value=st.session_state.final_title, key="refund_title_input_custom")
            refund_description = st.text_area("Refund Policy Description", value=st.session_state.get("final_description", ""), key="refund_desc_input_custom")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            refund_category = st.selectbox("Refund Policy Category", CATEGORY_OPTIONS, index=1, key="refund_category")
            if refund_category == "Other":
                custom_refund_category = st.text_input("Custom category", key="custom_refund_category")
        
        with col2:
            refund_event_type = st.selectbox("Refund Policy Event Type", EVENT_TYPE_OPTIONS + ["Gala"], index=1, key="refund_event_type")
            if refund_event_type == "Other":
                custom_refund_event_type = st.text_input("Custom event type", key="custom_refund_event_type")
        
        with col3:
            refund_tone = st.selectbox("Refund Policy Tone", TONE_OPTIONS + ["Playful"], index=1, key="refund_tone")
            if refund_tone == "Other":
                custom_refund_tone = st.text_input("Custom tone", key="custom_refund_tone")
        
        refund_context = st.text_input("Refund Policy Context (optional)", value=get_combined_context() or "", key="refund_context")
        refund_cost_mode = st.selectbox("Refund Policy Cost Mode", ["balanced", "economy", "premium"], key="refund_cost_mode")
        generate_refund_btn = st.form_submit_button("Generate Refund Policy")

    if generate_refund_btn:
        final_refund_category = custom_refund_category if refund_category == "Other" and custom_refund_category else refund_category
        final_refund_event_type = custom_refund_event_type if refund_event_type == "Other" and custom_refund_event_type else refund_event_type
        final_refund_tone = custom_refund_tone if refund_tone == "Other" and custom_refund_tone else refund_tone
        
        if not refund_description or refund_description.strip() == "":
            refund_description = f"A {final_refund_tone.lower()} {final_refund_category.lower()} {final_refund_event_type.lower()} event"
        
        with st.spinner("Generating refund policy with advanced prompt engineering..."):
            try:
                combined_context = get_combined_context()
                
                refund_policy, refund_logs = generate_refund_policy(
                    refund_title,
                    refund_description,
                    final_refund_category,
                    final_refund_event_type,
                    final_refund_tone,
                    combined_context,
                    refund_cost_mode
                )
                st.session_state.refund_policy = refund_policy
                st.session_state.refund_logs = refund_logs
            except Exception as e:
                st.error(f"Error generating refund policy: {str(e)}")
                st.error("Please try again or check your API key.")

    if st.session_state.get("refund_policy"):
        st.markdown("### Generated Refund Policy:")
        
        policy_text = st.session_state.refund_policy
        
        formatted_policy = policy_text.replace('\n\n', '\n').replace('\n', '<br/>')
        
        formatted_policy = formatted_policy.replace('1.', '<br/><strong>1.</strong>')
        formatted_policy = formatted_policy.replace('2.', '<br/><strong>2.</strong>')
        formatted_policy = formatted_policy.replace('3.', '<br/><strong>3.</strong>')
        formatted_policy = formatted_policy.replace('4.', '<br/><strong>4.</strong>')
        formatted_policy = formatted_policy.replace('5.', '<br/><strong>5.</strong>')
        formatted_policy = formatted_policy.replace('6.', '<br/><strong>6.</strong>')
        formatted_policy = formatted_policy.replace('7.', '<br/><strong>7.</strong>')
        formatted_policy = formatted_policy.replace('8.', '<br/><strong>8.</strong>')
        formatted_policy = formatted_policy.replace('9.', '<br/><strong>9.</strong>')
        
        if formatted_policy.startswith('<br/>'):
            formatted_policy = formatted_policy[5:]
        
        st.markdown(f'<div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #2563eb; color: #333; line-height: 1.6;"><strong>Refund Policy:</strong><br/><br/>{formatted_policy}</div>', unsafe_allow_html=True)
        st.download_button("Download Refund Policy", st.session_state.refund_policy, file_name="event_refund_policy.txt", mime="text/plain", key="download_refund_btn")
        
        display_current_context()
        show_context_input("Refund Policy Generation", "refund")
        
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
    st.markdown(st.session_state.final_refund_policy)
    
    st.markdown("---")
    
    summary_text = f"""EVENT SUMMARY

TITLE:
{st.session_state.final_title}

DESCRIPTION:
{st.session_state.final_description}

FREQUENTLY ASKED QUESTIONS:
{chr(10).join([f"• Q{i}: {faq['question']}{chr(10)}  Answer: {faq['answer']}{chr(10)}" for i, faq in enumerate(st.session_state.final_faqs, 1)])}

REFUND POLICY:
{st.session_state.final_refund_policy}

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

with st.expander("System Performance Analytics", expanded=False):
    st.markdown("### Global Performance Metrics")
    
    try:
        analytics_data = get_global_analytics()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Requests", analytics_data["total_requests"])
            st.metric("Cache Hit Rate", analytics_data["cache_hit_rate"])
        with col2:
            st.metric("Total Cost", analytics_data["total_cost"])
            st.metric("Cost Savings", analytics_data["cost_savings"])
        with col3:
            st.metric("Avg Response Time", analytics_data["avg_response_time"])
            st.metric("Error Rate", analytics_data["error_rate"])
        with col4:
            st.metric("Efficiency Score", analytics_data["efficiency_score"])
            st.metric("Total Tokens", analytics_data["total_tokens"])
        
        st.markdown("### Optimization Recommendations")
        for rec in analytics_data["recommendations"]:
            st.info(f"• {rec}")
        
        if st.button("Reset Analytics", key="reset_analytics"):
            reset_analytics()
            st.success("Analytics reset successfully!")
            st.rerun()
            
    except Exception as e:
        st.error(f"Analytics unavailable: {str(e)}")

st.markdown("---")
st.markdown("**Optimized for Scale:** Advanced caching, prompt optimization, and performance analytics for cost-effective scaling.")