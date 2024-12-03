import stocktrace as st

warning_log = st.Log('jaemothy', 'tests/', st.LOG_LEVEL.WARNING)
st.Logger.append_log(warning_log)

st.Logger.debug('jaemothy smells like poopy')
st.Logger.warning('carmen stinks (not true)')
st.Logger.critical('carmen is smelling like poopy (not true)')