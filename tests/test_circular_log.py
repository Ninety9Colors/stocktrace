import stocktrace as st

circle = st.CircularLog('test_circular', 'tests/circular/', max_log_count=0)

st.Logger.append_log(circle)
st.Logger.info('This shouldn\'t work! (in files)')