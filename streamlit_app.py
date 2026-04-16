import streamlit as st
import pandas as pd
import numpy as np

# 1. Set Page Title and Header
st.title("🚀 My First Streamlit App")
st.header("Welcome to the Demo")

# 2. Add Text and Markdown
st.write("Streamlit makes it easy to build interactive web interfaces using only Python.")
st.markdown("**Try interacting with the widgets below!**")

# 3. Add Input Widgets
name = st.text_input("Enter your name", placeholder="Type here...")
age = st.slider("Select your age", 0, 100, 25)

# 4. Use a Button to Trigger an Action
if st.button("Submit"):
    st.success(f"Hello {name}! You are {age} years old.")
    st.balloons()

# 5. Display a Simple Chart
st.subheader("Random Data Visualization")
chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['a', 'b', 'c']
)
st.line_chart(chart_data)

# 6. Add an Expander for Extra Info
with st.expander("See Raw Data"):
    st.write(chart_data)
