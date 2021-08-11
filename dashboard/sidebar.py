st.title("Tracking Public Unrest: USA")
st.sidebar.title("Public Unrest: Protests")
view = st.sidebar.radio('Select Timespan', ['Weekly', 'Annually'])
about_week = st.sidebar.beta_expander('About weekly')
with about_week:
    st.write("Use the search function to extract Google trends on public unrest related keywords from each state on a weekly basis. Find out how weekly trends correspond to the number of protests in each state.")

about_annual = st.sidebar.beta_expander('About annually')
with about_annual:
    st.write("Gain an annual overview of all public unrest in the US and the socio-economic and demographic conditions for each state.")
