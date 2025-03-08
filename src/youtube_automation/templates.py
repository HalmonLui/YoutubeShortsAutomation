import os
import json
import streamlit as st

TEMPLATES_FILE = 'templates.json'

def load_templates():
    """Load templates from the templates.json file."""
    if os.path.exists(TEMPLATES_FILE):
        try:
            with open(TEMPLATES_FILE, 'r') as f:
                return json.load(f)
        except:
            return {'templates': []}
    return {'templates': []}

def save_template(name, title_template, description_template):
    """Save a new template to the templates.json file."""
    templates = load_templates()
    templates['templates'].append({
        'name': name,
        'title': title_template,
        'description': description_template
    })
    with open(TEMPLATES_FILE, 'w') as f:
        json.dump(templates, f, indent=2)

def delete_template(name):
    """Delete a template from the templates.json file."""
    templates = load_templates()
    templates['templates'] = [t for t in templates['templates'] if t['name'] != name]
    with open(TEMPLATES_FILE, 'w') as f:
        json.dump(templates, f, indent=2)

def load_template_callback(template_name):
    """Callback function for loading a template."""
    templates = load_templates()
    template = next(t for t in templates['templates'] if t['name'] == template_name)
    # Store values in session state for next render
    st.session_state.next_title = template['title']
    st.session_state.next_description = template['description']

def render_template_manager():
    """Render the template manager UI in Streamlit."""
    # Initialize session state for next values if not present
    if 'next_title' not in st.session_state:
        st.session_state.next_title = st.session_state.title_template
    if 'next_description' not in st.session_state:
        st.session_state.next_description = st.session_state.description_template

    # Update the current values from next values if they exist
    st.session_state.title_template = st.session_state.next_title
    st.session_state.description_template = st.session_state.next_description

    st.subheader("Template Manager")
    
    # Load existing templates
    templates = load_templates()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Save Current Template")
        template_name = st.text_input("Template Name", key="save_template_name")
        if st.button("Save Template") and template_name:
            save_template(
                template_name,
                st.session_state.title_template,
                st.session_state.description_template
            )
            st.success(f"Template '{template_name}' saved!")
    
    with col2:
        st.write("Load Template")
        if templates['templates']:
            selected_template = st.selectbox(
                "Select Template",
                options=[t['name'] for t in templates['templates']],
                key="template_selector"
            )
            col3, col4 = st.columns(2)
            with col3:
                if st.button("Load", key="load_template_button", on_click=load_template_callback, args=(selected_template,)):
                    st.success("Template loaded!")
            with col4:
                if st.button("Delete", key="delete_template_button"):
                    delete_template(selected_template)
                    st.success(f"Template '{selected_template}' deleted!")
                    st.rerun() 