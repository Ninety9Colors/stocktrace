from stocktrace import Asset, AssetManager, CSV

AssetManager.get('AAPL')
AssetManager.get('MSFT')
AssetManager.get('AAPL').save_data()
AssetManager.get('MSFT').save_data()
print(AssetManager.get_assets())
# {'AAPL': Asset(AAPL, 1d), 'MSFT': Asset(MSFT, 1d)}

curr_date = AssetManager.get('AAPL').latest_date()
prev_date = AssetManager.get('AAPL').prev_date(curr_date)
print(f'{curr_date=}, {prev_date=}')

curr_cents = AssetManager.get('AAPL').latest_cents()
prev_cents = AssetManager.get('AAPL').get_cents(prev_date)
print(f'{curr_cents=}, {prev_cents=}')