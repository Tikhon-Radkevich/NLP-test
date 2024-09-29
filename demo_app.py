import streamlit as st

from utils.streamlit_utils import make_prediction, render_prediction


def main():
    user_input = st.text_input("Enter url:")
    try:
        prediction = make_prediction(user_input)
        render_prediction(prediction)
    except Exception as e:
        st.write(f"Error: {e}")


if __name__ == "__main__":
    main()
