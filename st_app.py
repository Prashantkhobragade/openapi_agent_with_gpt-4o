import streamlit as st
import json
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from tools.tool import unified_endpoint_connector
from azureai import AzureAI
from appconfig import AppConfig

# Load environment variables
load_dotenv()

# Create instances of AppConfig and AzureAI
config = AppConfig()
azure_ai = AzureAI(config)

# Set page title
st.set_page_config(page_title="SmartAPI Connect")
st.title("🤖 SmartAPI Connect")

# Sidebar for API key and base URL input
st.sidebar.header("Configuration")
base_url = st.sidebar.text_input("Enter Base URL or API URL")

# Store base_url in session state
if 'base_url' not in st.session_state:
    st.session_state['base_url'] = base_url

print("base url", base_url)

# File uploader for JSON file
uploaded_file = st.file_uploader("Choose a JSON file", type="json")

if uploaded_file is not None:
    try:
        data = json.loads(uploaded_file.getvalue())
        st.success("JSON file successfully loaded!")
    except json.JSONDecodeError:
        st.error("Invalid JSON file. Please upload a valid JSON file.")
        data = None

    if data:
        # Initialize LLM
        llm = azure_ai.get_client()
        
        # Define agents with optimized prompts

        api_smartconnect_agent = Agent(
            role="API Analyst and Caller",
            goal="""Analyze OpenAPI spec {data} for API structure, interpret user request {request}, 
                    identify appropriate API endpoints, and efficiently interact with these endpoints using 
                    the base url {base_url}. Handle all aspects of the API interaction process, from analysis 
                    to interpretation to call execution, including error handling.""",
            backstory="""As a versatile API specialist with over 20 years of experience, I excel in 
                    API architecture, natural language processing, API integration, and data structure 
                    comprehension. My expertise spans from analyzing API specifications and translating user 
                    requests into structured data to seamlessly interacting with diverse APIs across multiple 
                    domains.""",
            tools=[unified_endpoint_connector],
            verbose=True,
            llm=llm,
            allow_delegation=False
        )

        # Define tasks with focused outputs

        api_smartconnect_task = Task(
            description="""1. Analyze OpenAPI JSON data. Understand all endpoints, their purposes, parameters, request bodies, and response structures.
                        2. Interpret the user request {request}.
                        3. Identify the method, parameters, and determine which API endpoint(s) would be most appropriate to fulfill the user's needs.
                        4. Create a dynamic URL based on the identified parameters and appropriate endpoint.
                        5. Make the API call using the constructed URL.
                        6. Handle any errors gracefully, providing clear error messages (e.g., "Error 404: URL not found" for 404 errors).
                        7. Return the results of the API call or error message as appropriate.""",
            expected_output=""" The result of the API call. This should include::
                    - The constructed URL
                    - The result of the API call OR a clear error message if applicable""",
            agent=api_smartconnect_agent
        )


        # Create crew with parallel processing
        crew = Crew(
            agents=[api_smartconnect_agent],
            tasks=[api_smartconnect_task],
            #process=Process.sequential,
            verbose=True
        )

        # User input for request
        user_request = st.text_input("Enter your request:")

        if st.button("Process Request"):
            with st.spinner("Processing your request..."):
                try:
                    result = crew.kickoff(inputs={"data": data, "request": user_request, "base_url": st.session_state['base_url']})
                    st.success("Request processed successfully!")
                    with st.expander("View Complete output"):
                        st.write(result)
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.write("Please check your inputs and try again.")

else:
    st.info("Please upload a JSON file to begin.")