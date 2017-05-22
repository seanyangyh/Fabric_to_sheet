'''
請在環境變數新增 Fabirc帳號密碼
FABIRCUSER = 你的帳號
FABIRCPASSWORD = 你的密碼

下面三行也丟掉環境變數中
# Firefox 
PATH="/Users/mark/Downloads/geckodriver:$PATH"
export PATH

安裝火狐

'''
from collections import OrderedDict

# iOS or Android
PlatformName = 'Android'

# Top build version query raw data
Top_build = ['61600006']

# Get crash-free session only
Version = ['61600006', '61500002', '61400006', '61300002', '61200002', 'All Version']

'''
# iOS or Android
PlatformName = 'iOS'

# Top build version query raw data
Top_build = ['6.1.60.26']

# Get crash-free session only
Version = ['6.1.60.26', '6.1.50.18', '6.1.40.19', '6.1.30.22', '6.1.21.24', 'All Version']
'''

# Main criteria (if crash count > main criteria, it should be raised on the fabric tracking sheet.)
Criteria_count = 100

# Issue default assign
Default_status = 'Open'
Default_owner = 'Fate'
#Default_owner = 'Keith'

# Use spreadsheet_id to get "sheet" id - https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/get
# iOS Fabric sheet
#spreadsheet_id = '1ex2ovtXCVkZWuyqZi7awUYYxpK-uxioS-rOdyI6N_8E'
#sheet_id_all = '1927443904'
#sheet_id_summary = '670362750'
# sheet_id_template = '1898869629'

# Test sheet
spreadsheet_id = '1Gx_2izYogh-0PgEej-EtGJrYzUaL_Ci5N4OH0bQLblc'
sheet_id_all = '845833450'
sheet_id_summary = '362639746'
# sheet_id_template = '1403088925'
