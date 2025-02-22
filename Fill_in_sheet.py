from __future__ import print_function
from __future__ import division
import httplib2
import os
import datetime
import User_Input
import json
from time import sleep

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
# SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'


def PATH(p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), p))


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def json_parser(raw_data):
    # json -> dict of python
    json_data = json.loads(raw_data)
    return json_data


def sheet_summary_modify_handler_row_data(date, ver, crash_uv, crash_pv, dau, sheet_range):
    data = [
        {
            'values': [
                [date, ver, crash_uv, crash_pv, dau]
            ],
            'range': 'Summary!A' + str(sheet_range) + ':E' + str(sheet_range)
        },
    ]

    return data


def sheet_batchUpdate_handler(all_data, spreadsheet_id, service):
    batch_update_values_request_body = {
        'value_input_option': 'USER_ENTERED',
        'data': [
            all_data
        ]
    }
    result = service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=batch_update_values_request_body).execute()
    sleep(1)
    return result


def fabric_crash_rate_uploader(data, date, spreadsheet_id, sheet_range, service):
    multiple_batchUpdate_list = []
    for i in range(0, len(User_Input.Version), 1):
        crash_uv = data[User_Input.Version[i]]['CRASH-FREE USERS']
        crash_pv = data[User_Input.Version[i]]['CRASH-FREE SESSIONS']
        dau_data = data[User_Input.Version[i]]['User']
        multiple_batchUpdate_list.append(sheet_summary_modify_handler_row_data(date, User_Input.Version[i], crash_uv, crash_pv, dau_data, i+2))

    # append All Versions data
    crash_uv = data['All Version']['CRASH-FREE USERS']
    crash_pv = data['All Version']['CRASH-FREE SESSIONS']
    dau_data = data['All Version']['User']
    multiple_batchUpdate_list.append(sheet_summary_modify_handler_row_data(date, 'All Versions', crash_uv, crash_pv, dau_data, len(User_Input.Version)+2))

    if multiple_batchUpdate_list != []:
        modify_sheet = sheet_batchUpdate_handler(multiple_batchUpdate_list, spreadsheet_id, service)
        print(modify_sheet)
    else:
        print('There is no crash rate data to upload.')


def sheet_all_modify_row_data(data_ver, data_crash_count, data_history_crash_rate, data_history_occurrences, sheet_range):
    data = [
        {
            'values': [
                [data_ver]
            ],
            'range': 'All!B' + sheet_range
        },
        {
            'values': [
                [data_crash_count]
            ],
            'range': 'All!D' + sheet_range
        },
        {
            'values': [
                [data_history_crash_rate]
            ],
            'range': 'All!K' + sheet_range
        },
        {
            'values': [
                [data_history_occurrences]
            ],
            'range': 'All!L' + sheet_range
        }
    ]

    return data


def fabric_crashlytics_modifier(column_a_data, crash_rate_data, data, spreadsheet_id, service):
    temp_duplicate_list = []  # Temporary List to record the issue has been modified do not need raise again
    multiple_batchUpdate_list = []
    for i in range(0, len(column_a_data['values']), 1):
        for j in range(0, len(data['data']), 1):
            if column_a_data['values'][i][0] == data['data'][j]['IssueNumber']:
                ver = data['data'][j]['Version']
                crash_count = data['data'][j]['Crash'] + " / " + data['data'][j]['User']
                try:
                    h_occurrences, h_crash_rate_percent, h_crash_rate = history_occurrences_catcher(data['data'][j]['RecentActivity'], crash_rate_data)
                except:
                    print('There is no RecentActivity in' + data['data'][j]['IssueNumber'] + '.')
                    h_occurrences = 'None'
                    h_crash_rate_percent = 'None'
                multiple_batchUpdate_list.append(sheet_all_modify_row_data(ver, crash_count, h_crash_rate_percent, h_occurrences, str(i+1)))
                temp_duplicate_list.append(j)

    if multiple_batchUpdate_list !=[]:
        modify_sheet = sheet_batchUpdate_handler(multiple_batchUpdate_list, spreadsheet_id, service)
        print(modify_sheet)
    else:
        print('There is no fabric# should be modified.')

    print(temp_duplicate_list)
    return temp_duplicate_list


def is_today_exist_checker(today, sheet_range):
    for i in range(0, len(sheet_range['values']), 1):
        if sheet_range['values'][i][0] == today.strftime("%Y/%m/%d"):
            return True

    return False


def sheet_all_fill_color_and_merge(row, spreadsheet_id, service):
    # pythonDictionary = {'bold': True}
    # dictionaryToJson = json.dumps(pythonDictionary)

    batch_update_spreadsheet_request_color = {
        "requests": [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": User_Input.sheet_id_all,
                        "startRowIndex": row-1,
                        "endRowIndex": row,
                        "startColumnIndex": 0,
                        "endColumnIndex": 12
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {
                                "red": 1,
                                "green": 1,
                                "blue": 0
                            },
                            "horizontalAlignment": "LEFT",
                            "textFormat": {
                                "bold": "true"
                            }
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor, textFormat, horizontalAlignment)"
                }
            },
            {
                "mergeCells": {
                    "range": {
                        "sheetId": User_Input.sheet_id_all,
                        "startRowIndex": row-1,
                        "endRowIndex": row,
                        "startColumnIndex": 0,
                        "endColumnIndex": 12
                    },
                    "mergeType": "MERGE_ROWS"
                }
            }
        ]
    }
    result = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id,
                                                body=batch_update_spreadsheet_request_color).execute()
    sleep(1)
    return result


def sheet_all_append_date(date, spreadsheet_id, sheet_range, service):
    value_range_body = {
        'values': [
            [date],
        ]
    }
    result = service.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=sheet_range,
                                                     valueInputOption='USER_ENTERED', body=value_range_body).execute()
    sleep(1)
    print(result)
    begin_split = result['updates']['updatedRange'].split('!')
    second_split = begin_split[1].lstrip('A')
    row = int(second_split)
    result2 = sheet_all_fill_color_and_merge(row, spreadsheet_id, service)
    return result2


def split_version_by_diff_platform(ver, platform):
    if platform == 'iOS':
        ver_split = ver.split('.')
        ver_final = ver_split[0] + '.' + ver_split[1] + ver_split[2][:-1]
    elif platform == 'Android':
        ver_last = ver.index('(')
        ver_final = ver[:ver_last-1]

    return ver_final


def history_occurrences_catcher(RecentActivity, crash_rate_data):
    temp_list_count = ''
    ver = ''
    for i in range(0, len(User_Input.Version), 1):
        for j in range(0, len(RecentActivity), 1):
            if User_Input.Version[i] == RecentActivity[j]['Version']:
                temp_list_count = temp_list_count + RecentActivity[j]['Occurrences'] + ', '
                ver = ver + split_version_by_diff_platform(User_Input.Version[i], User_Input.PlatformName) + ', '

    temp_ver = ver[:-2]
    ver_list = temp_ver.split(', ')
    temp_list_count = temp_list_count[:-2]
    crash_count_list = temp_list_count.split(', ')
    for i in range(0, len(crash_count_list), 1):
        crash_count_list[i] = crash_count_list[i].replace('k', '000')

    print(crash_count_list)
    dau_list = []
    for i in range(0, len(User_Input.Version), 1):
        if split_version_by_diff_platform(User_Input.Version[i], User_Input.PlatformName) in ver_list:
            dau_list.append(crash_rate_data[User_Input.Version[i]]['User'])

    print(dau_list)
    temp_crash_rate = []
    for i in range(0, len(crash_count_list), 1):
        if dau_list[i] == '0':
            temp_crash_rate.append('dau=0')
        else:
            dau_list[i] = dau_list[i].replace(',', '')
            temp_crash_rate.append(str(float(crash_count_list[i]) / float(dau_list[i])))

    print(temp_crash_rate)
    temp_crash_rate_percent = ''
    for i in range(0, len(temp_crash_rate), 1):
        if temp_crash_rate[i] == 'dau=0':
            temp_crash_rate_percent = temp_crash_rate_percent + 'dau=0' + ', '
        else:
            temp_percent = "{:.2%}".format(float(temp_crash_rate[i]))
            temp_crash_rate_percent = temp_crash_rate_percent + temp_percent + ', '

    print(temp_ver + ' : ' + temp_list_count)
    print(temp_ver + ' : ' + temp_crash_rate_percent[:-2])
    return temp_ver + ' : ' + temp_list_count, temp_ver + ' : ' + temp_crash_rate_percent[:-2], temp_crash_rate


def sheet_all_append_handler_row_data(num, ver, url, crash_count, title, sub_title, h_crash_rate, h_occurrences):
    data = [num, ver, url, crash_count, User_Input.Default_owner, User_Input.Default_status, "", "", title, sub_title, h_crash_rate, h_occurrences]

    return data


def sheet_all_append_handler(all_data, spreadsheet_id, sheet_range, service):
    value_range_body = {
        'values': 
            all_data
    }
    print(value_range_body)
    result = service.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=sheet_range, valueInputOption='USER_ENTERED', body=value_range_body).execute()
    sleep(1)
    return result


def fabric_crashlytics_uploader(tf_today, today, duplicate_list, crash_rate_data, data, spreadsheet_id, sheet_range, service):
    first_time_count = 0
    multiple_batchUpdate_list = []
    for i in range(0, len(data['data']), 1):
        if i not in duplicate_list:
            if int(data['data'][i]['Crash'].replace('k', '000')) < 5 and User_Input.PlatformName == 'iOS':
                continue
            ver = data['data'][i]['Version']
            if ver in User_Input.Top_build[0].split('\n'):
                first_time_count += 1
                if first_time_count == 1 and tf_today is False:
                    sheet_all_append_date(today.strftime("%Y/%m/%d"), spreadsheet_id, sheet_range, service)
                num = data['data'][i]['IssueNumber']
                url = data['data'][i]['URL']
                crash_count = data['data'][i]['Crash'] + " / " + data['data'][i]['User']
                title = data['data'][i]['IssueTitle']
                sub_title = data['data'][i]['IssueSubtitle']
                try:
                    h_occurrences, h_crash_rate_percent, h_crash_rate = history_occurrences_catcher(data['data'][i]['RecentActivity'], crash_rate_data)
                except:
                    print('There is no RecentActivity in ' + num + '.')
                    h_occurrences = 'None'
                    h_crash_rate_percent = 'None'
                multiple_batchUpdate_list.append(sheet_all_append_handler_row_data(num, ver, url, crash_count, title, sub_title, h_crash_rate_percent, h_occurrences))

    if multiple_batchUpdate_list !=[]:
        append_sheet = sheet_all_append_handler(multiple_batchUpdate_list, spreadsheet_id, sheet_range, service)
        print(append_sheet)
    else:
        print('There is no new fabric# should be appended.')


def history_crash_rate_slope_calculator(crash_rate_data):
    crash_rate_data_filtered = [i for i in crash_rate_data if 'dau=0' not in i]
    if len(crash_rate_data_filtered) == 0 or len(crash_rate_data_filtered) == 1:
        return 1
    else:
        temp_slope_list = []
        for i in range(0, len(crash_rate_data_filtered)-1, 1):
            temp_slope = float(crash_rate_data_filtered[i]) / float(crash_rate_data_filtered[i + 1])
            temp_slope_list.append(temp_slope)

        print(temp_slope_list)
        return max(temp_slope_list)


def fabric_crashlytics_slope_criteria_uploader(tf_today, today, duplicate_list, crash_rate_data, data, spreadsheet_id, sheet_range, service):
    first_time_count = 0
    multiple_batchUpdate_list = []
    for i in range(0, len(data['data']), 1):
        if i not in duplicate_list and int(data['data'][i]['Crash'].replace('k', '000')) >= User_Input.Criteria_count:
            try:
                h_occurrences, h_crash_rate_percent, h_crash_rate = history_occurrences_catcher(data['data'][i]['RecentActivity'], crash_rate_data)
            except:
                print('There is no RecentActivity in ' + data['data'][i]['IssueNumber'] + '.')
                h_occurrences = 'None'
                h_crash_rate_percent = 'None'
                h_crash_rate = ['']
            h_slope = history_crash_rate_slope_calculator(h_crash_rate)
            print(h_slope)
            if h_slope >= User_Input.Slope:
                first_time_count += 1
                if first_time_count == 1 and tf_today is False:
                    sheet_all_append_date(today.strftime("%Y/%m/%d"), spreadsheet_id, sheet_range, service)
                ver = data['data'][i]['Version']
                num = data['data'][i]['IssueNumber']
                url = data['data'][i]['URL']
                crash_count = data['data'][i]['Crash'] + " / " + data['data'][i]['User']
                title = data['data'][i]['IssueTitle']
                sub_title = data['data'][i]['IssueSubtitle']
                multiple_batchUpdate_list.append(sheet_all_append_handler_row_data(num, ver, url, crash_count, title, sub_title, h_crash_rate_percent, h_occurrences))

    if multiple_batchUpdate_list !=[]:
        append_sheet = sheet_all_append_handler(multiple_batchUpdate_list, spreadsheet_id, sheet_range, service)
        print(append_sheet)
    else:
        print('There is no crash slope warning fabric# should be appended.')


def sheet_update_text_color_row_data(start_row, end_row, start_column, end_column, red, green, blue, sheet_id):
    data = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_row,
                    "endRowIndex": end_row,
                    "startColumnIndex": start_column,
                    "endColumnIndex": end_column
                },
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {
                            "foregroundColor": {
                                "red": red,
                                "green": green,
                                "blue": blue
                            }
                        }
                    }
                },
                "fields": "userEnteredFormat(textFormat)"
            }
        },
    ]

    return data


def sheet_update_text_color(all_data, spreadsheet_id, service):
    batch_update_spreadsheet_request_color = {
        "requests": [
            all_data
        ]
    }
    result = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=batch_update_spreadsheet_request_color).execute()
    sleep(1)
    return result


def crash_rate_warning_handler(column_d_data, spreadsheet_id, service):
    multiple_batchUpdate_list = []
    start_row = 0
    end_row = 99
    start_column = 3
    end_column = 4
    sheet_id = User_Input.sheet_id_summary
    update_text_color_all = sheet_update_text_color(sheet_update_text_color_row_data(start_row, end_row, start_column, end_column, 0, 0, 0, sheet_id), spreadsheet_id, service)
    print(update_text_color_all)

    for i in range(0, len(column_d_data), 1):
        crash_rate = column_d_data[i]
        if not crash_rate == []:
            temp = crash_rate[0]
            crash_rate_value = temp.rstrip('%')
            if float(crash_rate_value) <= 99.7:
                sheet_id = User_Input.sheet_id_summary
                multiple_batchUpdate_list.append(sheet_update_text_color_row_data(i+1, i+2, start_column, end_column, 1, 0, 0, sheet_id))

    if multiple_batchUpdate_list != []:
        update_text_color = sheet_update_text_color(multiple_batchUpdate_list, spreadsheet_id, service)
        print(update_text_color)
    else:
        print('There is NO crash rate higher then 0.3%.')


def fabric_warning_handler(column_d_data, spreadsheet_id, service):
    multiple_batchUpdate_list = []
    start_row = 0
    end_row = 9999
    start_column = 0
    end_column = 12
    sheet_id = User_Input.sheet_id_all
    update_text_color_all = sheet_update_text_color(sheet_update_text_color_row_data(start_row, end_row, start_column, end_column, 0, 0, 0, sheet_id), spreadsheet_id, service)
    print(update_text_color_all)

    for i in range(0, len(column_d_data), 1):
        crash_user = column_d_data[i]
        if not crash_user == []:
            temp = crash_user[0]
            crash_count = temp.strip().split(" / ")
            if int(crash_count[0].replace('k', '000')) >= 100:
                sheet_id = User_Input.sheet_id_all
                multiple_batchUpdate_list.append(sheet_update_text_color_row_data(i+1, i+2, start_column, end_column, 1, 0, 0, sheet_id))

    if multiple_batchUpdate_list != []:
        update_text_color = sheet_update_text_color(multiple_batchUpdate_list, spreadsheet_id, service)
        print(update_text_color)
    else:
        print('There is no crash count >= 100 case.')


def fabric_slope_warning_handler(column_k_data, spreadsheet_id, service):
    multiple_batchUpdate_list = []
    start_column = 0
    end_column = 12
    for i in range(0, len(column_k_data), 1):
        ver_crash_rate = column_k_data[i]
        if not ver_crash_rate == []:
            if not ver_crash_rate[0] == 'None':
                crash_rate = ver_crash_rate[0].split(" : ")
                temp = crash_rate[1].replace('%', '')
                h_crash_rate = temp.split(", ")
                for j in range(0, len(h_crash_rate), 1):
                    if h_crash_rate[j] == '0.00':
                        h_crash_rate[j] = '0.01'
                h_slope = history_crash_rate_slope_calculator(h_crash_rate)
                if h_slope >= User_Input.Slope:
                    sheet_id = User_Input.sheet_id_all
                    multiple_batchUpdate_list.append(sheet_update_text_color_row_data(i+1, i+2, start_column, end_column, 1, 0.5, 0, sheet_id))

    if multiple_batchUpdate_list != []:
        update_text_color = sheet_update_text_color(multiple_batchUpdate_list, spreadsheet_id, service)
        print(update_text_color)
    else:
        print('There is no crash rate slope >= ' + User_Input.Slope + ' case.')


def main():
    today = datetime.datetime.now()
    print(today.strftime("%Y/%m/%d"))

    # Oauth Credential from client_secret.json
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

    # Sheet_ID from the url
    spreadsheet_id = User_Input.spreadsheet_id

    # Define range
    range_all = 'All!A2:L'
    range_all_column_a = 'All!A:A'
    range_all_column_d = 'All!D'
    range_all_column_k = 'All!K'
    range_summary = 'Summary!A2:E'
    range_summary_column_d = 'Summary!D2:D'

    # read Fabric.json
    read_fabric = open(str(PATH('./Fabric.json')), "r")
    raw_data = read_fabric.read()
    read_fabric.close()
    # crash rate parser
    crash_rate_dict = json_parser(raw_data)
    print(crash_rate_dict)
    # upload crash rate data to sheet
    fabric_crash_rate_uploader(crash_rate_dict, today.strftime("%Y/%m/%d"), spreadsheet_id, range_summary, service)

    # read Top_build_Fabric.json
    read_crashlytics = open(str(PATH('./Top_build_Fabric.json')), "r")
    raw_data_crashlytics = read_crashlytics.read()
    read_crashlytics.close()
    # crashlytics parser
    crashlytics_dict = json_parser(raw_data_crashlytics)
    print(crashlytics_dict)

    if crashlytics_dict == {}:
        # if Top_build_Fabric.json has no data for analysis, just bypass and finish
        pass
    else:
        # get column A data, prepare for checking today exist/column A and json comparison via modifier
        column_a_data = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_all_column_a).execute()
        sleep(1)
        print(column_a_data)
        # upload detail crash data to All sheet
        is_today = is_today_exist_checker(today, column_a_data)
        duplicated_list = fabric_crashlytics_modifier(column_a_data, crash_rate_dict, crashlytics_dict, spreadsheet_id, service)
        fabric_crashlytics_uploader(is_today, today, duplicated_list, crash_rate_dict, crashlytics_dict, spreadsheet_id, range_all, service)

        # get column A data again for checking today exist in column A or not
        column_a_data = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_all_column_a).execute()
        sleep(1)
        print(column_a_data)
        is_today = is_today_exist_checker(today, column_a_data)
        # upload slope method crash data to All sheet
        fabric_crashlytics_slope_criteria_uploader(is_today, today, duplicated_list, crash_rate_dict, crashlytics_dict, spreadsheet_id, range_all, service)

        # get Summary sheet column D data to find crash rate above 0.3% and mark as red
        summary_column_d_data = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_summary_column_d).execute()
        sleep(1)
        print(summary_column_d_data)
        crash_rate_warning_handler(summary_column_d_data['values'], spreadsheet_id, service)

        # get All sheet column D data to find crash count above 100 and mark as red
        column_d_data = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_all_column_d + "2:D").execute()
        sleep(1)
        print(column_d_data)
        fabric_warning_handler(column_d_data['values'], spreadsheet_id, service)

        # get All sheet column K data to find crash rate slope above 1.2 and mark as orange
        column_k_data = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_all_column_k + "2:K").execute()
        sleep(1)
        print(column_k_data)
        fabric_slope_warning_handler(column_k_data['values'], spreadsheet_id, service)


if __name__ == '__main__':
    main()
