import datetime as dt
import stocktrace as st

st.FileManager.init()

test_path = 'tests/test_append_file.log'
test_message = f'{dt.datetime.now(st.TIMEZONE)} INFO TEST!!!!'

query = st.FileQuery(test_path)
st.FileManager.append_file(query, test_message)